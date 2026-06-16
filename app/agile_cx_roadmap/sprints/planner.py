from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

import psycopg
from psycopg.rows import dict_row


@dataclass(frozen=True)
class SprintCandidate:
    backlog_item_id: int
    title: str
    product_area: str
    status: str
    priority_score: float
    rice_score: float
    effort_points: int
    affected_customers: int
    avg_csat: float


@dataclass(frozen=True)
class SprintPlanItem:
    planned_order: int
    backlog_item_id: int
    title: str
    product_area: str
    priority_score: float
    rice_score: float
    effort_points: int


@dataclass(frozen=True)
class SprintPlan:
    sprint_id: int | None
    sprint_name: str
    sprint_goal: str
    start_date: date
    end_date: date
    capacity_points: int
    committed_points: int
    selected_items: list[SprintPlanItem]
    skipped_items: list[SprintCandidate]
    action: str


def to_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def fetch_next_sprint_defaults(
    conn: psycopg.Connection,
) -> tuple[int, date]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT
                COUNT(*) + 1 AS next_sprint_number,
                COALESCE(
                    (MAX(end_date) + INTERVAL '1 day')::DATE,
                    CURRENT_DATE
                ) AS suggested_start_date
            FROM sprints;
            """
        )
        row = cur.fetchone()

    if row is None:
        return 1, date.today()

    return int(row["next_sprint_number"]), row["suggested_start_date"]


def fetch_candidates(
    conn: psycopg.Connection,
    limit: int | None,
) -> list[SprintCandidate]:
    params: list[Any] = []

    limit_clause = ""
    if limit is not None:
        limit_clause = "LIMIT %s"
        params.append(limit)

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"""
            SELECT
                bi.backlog_item_id,
                bi.title,
                pa.name AS product_area,
                bi.status,
                bi.priority_score,
                bi.rice_score,
                bi.effort_points,
                ft.affected_customers,
                ft.avg_csat
            FROM backlog_items bi
            JOIN product_areas pa
                ON bi.product_area_id = pa.product_area_id
            JOIN feedback_themes ft
                ON bi.theme_id = ft.theme_id
            WHERE bi.status IN ('backlog', 'ready')
              AND NOT EXISTS (
                  SELECT 1
                  FROM sprint_items si
                  WHERE si.backlog_item_id = bi.backlog_item_id
              )
            ORDER BY
                bi.priority_score DESC,
                bi.rice_score DESC,
                bi.effort_points ASC
            {limit_clause};
            """,
            params,
        )
        rows = cur.fetchall()

    return [
        SprintCandidate(
            backlog_item_id=int(row["backlog_item_id"]),
            title=str(row["title"]),
            product_area=str(row["product_area"]),
            status=str(row["status"]),
            priority_score=to_float(row["priority_score"]),
            rice_score=to_float(row["rice_score"]),
            effort_points=int(row["effort_points"]),
            affected_customers=int(row["affected_customers"]),
            avg_csat=to_float(row["avg_csat"]),
        )
        for row in rows
    ]


def build_sprint_name(sprint_number: int) -> str:
    return f"Sprint {sprint_number} - CX Roadmap Execution"


def build_sprint_goal(selected_items: list[SprintPlanItem]) -> str:
    if not selected_items:
        return "No sprint goal generated because no backlog items fit the capacity."

    product_area_counts = Counter(item.product_area for item in selected_items)
    top_areas = [area for area, _count in product_area_counts.most_common(2)]
    area_text = " and ".join(top_areas)

    return (
        f"Reduce customer friction across {area_text} by delivering "
        f"{len(selected_items)} evidence-backed backlog items selected from "
        "CX priority and RICE scoring."
    )


def build_plan(
    candidates: list[SprintCandidate],
    sprint_number: int,
    start_date: date,
    duration_days: int,
    capacity_points: int,
) -> SprintPlan:
    selected_items = []
    skipped_items = []
    committed_points = 0

    for candidate in candidates:
        next_total = committed_points + candidate.effort_points

        if next_total <= capacity_points:
            selected_items.append(
                SprintPlanItem(
                    planned_order=len(selected_items) + 1,
                    backlog_item_id=candidate.backlog_item_id,
                    title=candidate.title,
                    product_area=candidate.product_area,
                    priority_score=candidate.priority_score,
                    rice_score=candidate.rice_score,
                    effort_points=candidate.effort_points,
                )
            )
            committed_points = next_total
        else:
            skipped_items.append(candidate)

    return SprintPlan(
        sprint_id=None,
        sprint_name=build_sprint_name(sprint_number),
        sprint_goal=build_sprint_goal(selected_items),
        start_date=start_date,
        end_date=start_date + timedelta(days=duration_days - 1),
        capacity_points=capacity_points,
        committed_points=committed_points,
        selected_items=selected_items,
        skipped_items=skipped_items,
        action="would_create",
    )


def fetch_table_columns(
    conn: psycopg.Connection,
    table_name: str,
) -> set[str]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s;
            """,
            (table_name,),
        )
        rows = cur.fetchall()

    return {str(row["column_name"]) for row in rows}


def create_sprint(
    conn: psycopg.Connection,
    plan: SprintPlan,
) -> int:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            INSERT INTO sprints (
                sprint_name,
                sprint_goal,
                start_date,
                end_date,
                status,
                capacity_points,
                committed_points,
                completed_points
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING sprint_id;
            """,
            (
                plan.sprint_name,
                plan.sprint_goal,
                plan.start_date,
                plan.end_date,
                "active",
                plan.capacity_points,
                plan.committed_points,
                0,
            ),
        )
        row = cur.fetchone()

    if row is None:
        raise RuntimeError("Sprint insert failed.")

    return int(row["sprint_id"])


def create_sprint_item(
    conn: psycopg.Connection,
    sprint_id: int,
    item: SprintPlanItem,
) -> None:
    sprint_item_columns = fetch_table_columns(conn, "sprint_items")

    payload: dict[str, Any] = {
        "sprint_id": sprint_id,
        "backlog_item_id": item.backlog_item_id,
        "story_points": item.effort_points,
        "status": "to_do",
        "blocked_flag": False,
    }

    ordered_columns = [
        column
        for column in [
            "sprint_id",
            "backlog_item_id",
            "story_points",
            "status",
            "blocked_flag",
        ]
        if column in sprint_item_columns
    ]

    if "sprint_id" not in ordered_columns or "backlog_item_id" not in ordered_columns:
        raise RuntimeError("sprint_items table is missing required columns.")

    placeholders = ", ".join(["%s"] * len(ordered_columns))
    column_sql = ", ".join(ordered_columns)
    values = [payload[column] for column in ordered_columns]

    with conn.cursor() as cur:
        cur.execute(
            f"""
            INSERT INTO sprint_items ({column_sql})
            VALUES ({placeholders});
            """,
            values,
        )


def apply_plan(
    conn: psycopg.Connection,
    plan: SprintPlan,
) -> SprintPlan:
    sprint_id = create_sprint(conn, plan)

    for item in plan.selected_items:
        create_sprint_item(conn, sprint_id, item)

    return SprintPlan(
        sprint_id=sprint_id,
        sprint_name=plan.sprint_name,
        sprint_goal=plan.sprint_goal,
        start_date=plan.start_date,
        end_date=plan.end_date,
        capacity_points=plan.capacity_points,
        committed_points=plan.committed_points,
        selected_items=plan.selected_items,
        skipped_items=plan.skipped_items,
        action="created",
    )


def plan_sprint(
    database_url: str,
    dry_run: bool,
    capacity_points: int,
    duration_days: int,
    start_date_override: date | None = None,
    candidate_limit: int | None = None,
) -> SprintPlan:
    with psycopg.connect(database_url) as conn:
        sprint_number, suggested_start_date = fetch_next_sprint_defaults(conn)
        start_date = start_date_override or suggested_start_date
        candidates = fetch_candidates(conn, limit=candidate_limit)

        plan = build_plan(
            candidates=candidates,
            sprint_number=sprint_number,
            start_date=start_date,
            duration_days=duration_days,
            capacity_points=capacity_points,
        )

        if dry_run:
            conn.rollback()
            return plan

        applied_plan = apply_plan(conn, plan)
        conn.commit()
        return applied_plan
