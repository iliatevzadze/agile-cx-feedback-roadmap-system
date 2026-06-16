from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from re import sub
from typing import Any

import psycopg
from psycopg.rows import dict_row


@dataclass(frozen=True)
class SprintReportResult:
    sprint_id: int
    sprint_name: str
    output_path: Path
    item_count: int
    committed_points: int
    completed_points: int
    completion_rate: float


def to_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def to_int(value: Any) -> int:
    if value is None:
        return 0
    return int(value)


def money(value: float) -> str:
    return f"${value:,.2f}"


def percent(value: float) -> str:
    return f"{value:.2f}%"


def clean_cell(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", "<br>")


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    if not rows:
        return "_No rows found._"

    header_line = "| " + " | ".join(headers) + " |"
    divider_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    row_lines = [
        "| " + " | ".join(clean_cell(value) for value in row) + " |"
        for row in rows
    ]

    return "\n".join([header_line, divider_line, *row_lines])


def slugify(value: str) -> str:
    slug = sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug or "sprint-report"


def fetch_latest_sprint_id(conn: psycopg.Connection) -> int:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT sprint_id
            FROM sprints
            ORDER BY sprint_id DESC
            LIMIT 1;
            """
        )
        row = cur.fetchone()

    if row is None:
        raise RuntimeError("No sprints found.")

    return int(row["sprint_id"])


def fetch_sprint(
    conn: psycopg.Connection,
    sprint_id: int,
) -> dict[str, Any]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT
                sprint_id,
                sprint_name,
                sprint_goal,
                start_date,
                end_date,
                status,
                capacity_points,
                committed_points,
                completed_points
            FROM sprints
            WHERE sprint_id = %s;
            """,
            (sprint_id,),
        )
        row = cur.fetchone()

    if row is None:
        raise RuntimeError(f"Sprint {sprint_id} was not found.")

    return dict(row)


def fetch_sprint_items(
    conn: psycopg.Connection,
    sprint_id: int,
) -> list[dict[str, Any]]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT
                si.sprint_item_id,
                si.sprint_id,
                si.backlog_item_id,
                bi.title,
                pa.name AS product_area,
                si.story_points,
                bi.priority_score,
                bi.rice_score,
                si.status,
                si.blocked_flag,
                ft.affected_customers,
                ft.affected_arr,
                ft.avg_csat,
                ft.sla_breach_count,
                ft.churn_risk_count
            FROM sprint_items si
            JOIN backlog_items bi
                ON si.backlog_item_id = bi.backlog_item_id
            JOIN product_areas pa
                ON bi.product_area_id = pa.product_area_id
            JOIN feedback_themes ft
                ON bi.theme_id = ft.theme_id
            WHERE si.sprint_id = %s
            ORDER BY si.sprint_item_id;
            """,
            (sprint_id,),
        )
        rows = cur.fetchall()

    return [dict(row) for row in rows]


def fetch_release_impact(
    conn: psycopg.Connection,
    sprint_id: int,
) -> list[dict[str, Any]]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT
                bi.backlog_item_id,
                bi.title,
                pa.name AS product_area,
                ri.before_ticket_volume,
                ri.after_ticket_volume,
                ri.before_ticket_volume - ri.after_ticket_volume
                    AS ticket_reduction,
                ri.before_avg_csat,
                ri.after_avg_csat,
                ri.after_avg_csat - ri.before_avg_csat AS csat_change,
                ri.before_sla_breach_rate,
                ri.after_sla_breach_rate,
                ri.before_sla_breach_rate - ri.after_sla_breach_rate
                    AS sla_breach_rate_reduction,
                ri.measured_at
            FROM sprint_items si
            JOIN backlog_items bi
                ON si.backlog_item_id = bi.backlog_item_id
            JOIN product_areas pa
                ON bi.product_area_id = pa.product_area_id
            JOIN release_impact ri
                ON bi.backlog_item_id = ri.backlog_item_id
            WHERE si.sprint_id = %s
            ORDER BY ticket_reduction DESC, csat_change DESC;
            """,
            (sprint_id,),
        )
        rows = cur.fetchall()

    return [dict(row) for row in rows]


def fetch_retro_items(
    conn: psycopg.Connection,
    sprint_id: int,
) -> list[dict[str, Any]]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT *
            FROM retro_items
            WHERE sprint_id = %s
            ORDER BY retro_item_id;
            """,
            (sprint_id,),
        )
        rows = cur.fetchall()

    return [dict(row) for row in rows]


def status_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}

    for item in items:
        status = str(item["status"])
        counts[status] = counts.get(status, 0) + 1

    return counts


def product_area_summary(items: list[dict[str, Any]]) -> list[list[Any]]:
    grouped: dict[str, dict[str, Any]] = {}

    for item in items:
        area = str(item["product_area"])

        if area not in grouped:
            grouped[area] = {
                "items": 0,
                "points": 0,
                "customers": 0,
                "arr": 0.0,
            }

        grouped[area]["items"] += 1
        grouped[area]["points"] += to_int(item["story_points"])
        grouped[area]["customers"] += to_int(item["affected_customers"])
        grouped[area]["arr"] += to_float(item["affected_arr"])

    rows = []

    for area, values in sorted(grouped.items()):
        rows.append(
            [
                area,
                values["items"],
                values["points"],
                values["customers"],
                money(values["arr"]),
            ]
        )

    return rows


def build_executive_summary(
    sprint: dict[str, Any],
    items: list[dict[str, Any]],
) -> list[str]:
    committed_points = to_int(sprint["committed_points"])
    completed_points = to_int(sprint["completed_points"])
    capacity_points = to_int(sprint["capacity_points"])
    completion_rate = 0.0

    if committed_points:
        completion_rate = (completed_points / committed_points) * 100

    blocked_count = sum(1 for item in items if item["blocked_flag"])
    affected_customers = sum(to_int(item["affected_customers"]) for item in items)
    affected_arr = sum(to_float(item["affected_arr"]) for item in items)

    return [
        f"- Sprint status: **{sprint['status']}**",
        f"- Capacity: **{capacity_points} points**",
        f"- Committed: **{committed_points} points**",
        f"- Completed: **{completed_points} points**",
        f"- Completion rate: **{percent(completion_rate)}**",
        f"- Sprint backlog items: **{len(items)}**",
        f"- Blocked items: **{blocked_count}**",
        f"- Customers represented by selected work: **{affected_customers}**",
        f"- ARR represented by selected work: **{money(affected_arr)}**",
    ]


def render_status_breakdown(items: list[dict[str, Any]]) -> str:
    counts = status_counts(items)
    rows = [[status, count] for status, count in sorted(counts.items())]
    return markdown_table(["Status", "Item Count"], rows)


def render_sprint_items(items: list[dict[str, Any]]) -> str:
    rows = []

    for item in items:
        rows.append(
            [
                item["backlog_item_id"],
                item["title"],
                item["product_area"],
                item["story_points"],
                f"{to_float(item['priority_score']):.2f}",
                f"{to_float(item['rice_score']):.2f}",
                item["status"],
                "yes" if item["blocked_flag"] else "no",
            ]
        )

    return markdown_table(
        [
            "Backlog ID",
            "Title",
            "Product Area",
            "Points",
            "CX Priority",
            "RICE",
            "Status",
            "Blocked",
        ],
        rows,
    )


def render_product_area_summary(items: list[dict[str, Any]]) -> str:
    return markdown_table(
        [
            "Product Area",
            "Items",
            "Story Points",
            "Affected Customers",
            "Affected ARR",
        ],
        product_area_summary(items),
    )


def render_release_impact(impact_rows: list[dict[str, Any]]) -> str:
    rows = []

    for row in impact_rows:
        rows.append(
            [
                row["backlog_item_id"],
                row["title"],
                row["product_area"],
                row["before_ticket_volume"],
                row["after_ticket_volume"],
                row["ticket_reduction"],
                f"{to_float(row['csat_change']):.2f}",
                f"{to_float(row['sla_breach_rate_reduction']):.2f}",
            ]
        )

    return markdown_table(
        [
            "Backlog ID",
            "Title",
            "Product Area",
            "Before Tickets",
            "After Tickets",
            "Ticket Reduction",
            "CSAT Change",
            "SLA Breach Rate Reduction",
        ],
        rows,
    )


def render_retro_items(retro_rows: list[dict[str, Any]]) -> str:
    if not retro_rows:
        return "_No retrospective items recorded for this sprint._"

    visible_columns = [
        column
        for column in [
            "retro_type",
            "category",
            "item_type",
            "summary",
            "description",
            "action_item",
            "owner",
            "status",
        ]
        if column in retro_rows[0]
    ]

    if not visible_columns:
        visible_columns = [
            column
            for column in retro_rows[0]
            if column not in {"retro_item_id", "sprint_id", "created_at"}
        ]

    rows = []

    for row in retro_rows:
        rows.append([row.get(column, "") for column in visible_columns])

    headers = [column.replace("_", " ").title() for column in visible_columns]
    return markdown_table(headers, rows)


def build_report_markdown(
    sprint: dict[str, Any],
    items: list[dict[str, Any]],
    release_impact: list[dict[str, Any]],
    retro_items: list[dict[str, Any]],
) -> str:
    sprint_id = int(sprint["sprint_id"])
    sprint_name = str(sprint["sprint_name"])

    lines = [
        f"# Sprint Review and Retrospective Report: {sprint_name}",
        "",
        "## Sprint Metadata",
        "",
        f"- Sprint ID: **{sprint_id}**",
        f"- Sprint name: **{sprint_name}**",
        f"- Sprint goal: **{sprint['sprint_goal']}**",
        f"- Start date: **{sprint['start_date']}**",
        f"- End date: **{sprint['end_date']}**",
        f"- Status: **{sprint['status']}**",
        "",
        "## Executive Summary",
        "",
        *build_executive_summary(sprint, items),
        "",
        "## Sprint Item Status Breakdown",
        "",
        render_status_breakdown(items),
        "",
        "## Sprint Backlog Items",
        "",
        render_sprint_items(items),
        "",
        "## Product Area Coverage",
        "",
        render_product_area_summary(items),
        "",
        "## Release Impact Linked to Sprint Items",
        "",
        render_release_impact(release_impact),
        "",
        "## Retrospective Notes",
        "",
        render_retro_items(retro_items),
        "",
        "## Agile Interpretation",
        "",
        "- This report connects CX evidence to sprint execution.",
        "- It shows whether planned work fit the sprint capacity.",
        "- It highlights blocked or unfinished work for follow-up.",
        "- It links released work to post-release support impact where available.",
        "- It creates a review artifact that Product, Support and CX teams can use.",
        "",
    ]

    return "\n".join(lines)


def write_report(
    output_dir: Path,
    sprint: dict[str, Any],
    markdown: str,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    sprint_id = int(sprint["sprint_id"])
    sprint_name = str(sprint["sprint_name"])
    filename = f"sprint-{sprint_id}-{slugify(sprint_name)}-review.md"
    output_path = output_dir / filename
    output_path.write_text(markdown, encoding="utf-8")

    return output_path


def generate_sprint_report(
    database_url: str,
    output_dir: Path,
    sprint_id: int | None = None,
) -> SprintReportResult:
    with psycopg.connect(database_url) as conn:
        selected_sprint_id = sprint_id or fetch_latest_sprint_id(conn)
        sprint = fetch_sprint(conn, selected_sprint_id)
        items = fetch_sprint_items(conn, selected_sprint_id)
        release_impact = fetch_release_impact(conn, selected_sprint_id)
        retro_items = fetch_retro_items(conn, selected_sprint_id)

    markdown = build_report_markdown(
        sprint=sprint,
        items=items,
        release_impact=release_impact,
        retro_items=retro_items,
    )

    output_path = write_report(
        output_dir=output_dir,
        sprint=sprint,
        markdown=markdown,
    )

    committed_points = to_int(sprint["committed_points"])
    completed_points = to_int(sprint["completed_points"])
    completion_rate = 0.0

    if committed_points:
        completion_rate = (completed_points / committed_points) * 100

    return SprintReportResult(
        sprint_id=int(sprint["sprint_id"]),
        sprint_name=str(sprint["sprint_name"]),
        output_path=output_path,
        item_count=len(items),
        committed_points=committed_points,
        completed_points=to_int(sprint["completed_points"]),
        completion_rate=completion_rate,
    )
