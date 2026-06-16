from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd
import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row


def get_database_url() -> str:
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is missing. Create .env from .env.example.")

    return database_url


def run_query(sql: str, params: tuple[Any, ...] | None = None) -> pd.DataFrame:
    database_url = get_database_url()

    with psycopg.connect(database_url) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params or ())
            rows = cur.fetchall()

    return pd.DataFrame([dict(row) for row in rows])


def get_kpis() -> dict[str, Any]:
    df = run_query(
        """
        SELECT
            (SELECT COUNT(*) FROM support_tickets) AS total_tickets,
            (SELECT COUNT(*) FROM feedback_themes) AS feedback_themes,
            (SELECT COUNT(*) FROM backlog_items) AS backlog_items,
            (SELECT COUNT(*) FROM sprints) AS sprints,
            (SELECT COUNT(*) FROM sprints WHERE status = 'active') AS active_sprints,
            (SELECT COUNT(*) FROM support_tickets WHERE sla_breached = TRUE)
                AS sla_breached_tickets,
            (SELECT ROUND(AVG(csat_score)::NUMERIC, 2) FROM support_tickets)
                AS avg_ticket_csat,
            (SELECT ROUND(SUM(affected_arr)::NUMERIC, 2) FROM feedback_themes)
                AS total_affected_arr;
        """
    )

    if df.empty:
        return {}

    return df.iloc[0].to_dict()


def get_theme_summary() -> pd.DataFrame:
    return run_query(
        """
        SELECT
            ft.theme_id,
            pa.name AS product_area,
            pa.owner_team,
            ft.theme_name,
            ft.frequency_count,
            ft.affected_customers,
            ROUND(ft.affected_arr::NUMERIC, 2) AS affected_arr,
            ft.avg_csat,
            ft.escalation_count,
            ft.sla_breach_count,
            ft.churn_risk_count,
            bi.priority_score,
            bi.rice_score
        FROM feedback_themes ft
        JOIN product_areas pa
            ON ft.product_area_id = pa.product_area_id
        LEFT JOIN backlog_items bi
            ON ft.theme_id = bi.theme_id
        ORDER BY
            bi.priority_score DESC,
            ft.affected_arr DESC;
        """
    )


def get_backlog_priority() -> pd.DataFrame:
    return run_query(
        """
        SELECT
            bi.backlog_item_id,
            bi.title,
            pa.name AS product_area,
            bi.status,
            bi.effort_points,
            bi.priority_score,
            bi.rice_score,
            bi.severity_score,
            bi.frequency_score,
            bi.customer_impact_score,
            bi.revenue_impact_score,
            bi.sla_risk_score,
            bi.csat_impact_score,
            bi.churn_risk_score,
            bi.workaround_score
        FROM backlog_items bi
        JOIN product_areas pa
            ON bi.product_area_id = pa.product_area_id
        ORDER BY
            bi.priority_score DESC,
            bi.rice_score DESC,
            bi.effort_points ASC;
        """
    )


def get_sprint_health() -> pd.DataFrame:
    return run_query(
        """
        SELECT
            s.sprint_id,
            s.sprint_name,
            s.sprint_goal,
            s.start_date,
            s.end_date,
            s.status,
            s.capacity_points,
            s.committed_points,
            s.completed_points,
            ROUND(
                CASE
                    WHEN s.committed_points = 0 THEN 0
                    ELSE (
                        s.completed_points::NUMERIC
                        / s.committed_points::NUMERIC
                    ) * 100
                END,
                2
            ) AS completion_rate_percent,
            COUNT(si.sprint_item_id) AS sprint_item_count,
            COUNT(si.sprint_item_id)
                FILTER (WHERE si.status = 'to_do') AS to_do_items,
            COUNT(si.sprint_item_id)
                FILTER (WHERE si.status = 'in_progress') AS in_progress_items,
            COUNT(si.sprint_item_id)
                FILTER (WHERE si.status = 'qa') AS qa_items,
            COUNT(si.sprint_item_id)
                FILTER (WHERE si.status = 'done') AS done_items,
            COUNT(si.sprint_item_id)
                FILTER (WHERE si.status = 'released') AS released_items,
            COUNT(si.sprint_item_id)
                FILTER (WHERE si.blocked_flag = TRUE) AS blocked_items
        FROM sprints s
        LEFT JOIN sprint_items si
            ON s.sprint_id = si.sprint_id
        GROUP BY
            s.sprint_id,
            s.sprint_name,
            s.sprint_goal,
            s.start_date,
            s.end_date,
            s.status,
            s.capacity_points,
            s.committed_points,
            s.completed_points
        ORDER BY
            s.start_date DESC,
            s.sprint_id DESC;
        """
    )


def get_sprint_items(sprint_id: int | None = None) -> pd.DataFrame:
    where_clause = ""
    params: tuple[Any, ...] = ()

    if sprint_id is not None:
        where_clause = "WHERE si.sprint_id = %s"
        params = (sprint_id,)

    return run_query(
        f"""
        SELECT
            si.sprint_id,
            si.sprint_item_id,
            si.backlog_item_id,
            bi.title,
            pa.name AS product_area,
            si.story_points,
            bi.priority_score,
            bi.rice_score,
            si.status,
            si.blocked_flag
        FROM sprint_items si
        JOIN backlog_items bi
            ON si.backlog_item_id = bi.backlog_item_id
        JOIN product_areas pa
            ON bi.product_area_id = pa.product_area_id
        {where_clause}
        ORDER BY
            si.sprint_id DESC,
            si.sprint_item_id;
        """,
        params,
    )


def get_release_impact() -> pd.DataFrame:
    return run_query(
        """
        SELECT
            bi.backlog_item_id,
            bi.title,
            pa.name AS product_area,
            ri.before_ticket_volume,
            ri.after_ticket_volume,
            ri.before_ticket_volume - ri.after_ticket_volume
                AS ticket_reduction,
            ROUND(
                CASE
                    WHEN ri.before_ticket_volume = 0 THEN 0
                    ELSE (
                        (ri.before_ticket_volume - ri.after_ticket_volume)::NUMERIC
                        / ri.before_ticket_volume::NUMERIC
                    ) * 100
                END,
                2
            ) AS ticket_reduction_percent,
            ri.before_avg_csat,
            ri.after_avg_csat,
            ROUND(ri.after_avg_csat - ri.before_avg_csat, 2) AS csat_change,
            ri.before_sla_breach_rate,
            ri.after_sla_breach_rate,
            ROUND(
                ri.before_sla_breach_rate - ri.after_sla_breach_rate,
                2
            ) AS sla_breach_rate_reduction,
            ri.measured_at
        FROM release_impact ri
        JOIN backlog_items bi
            ON ri.backlog_item_id = bi.backlog_item_id
        JOIN product_areas pa
            ON ri.product_area_id = pa.product_area_id
        ORDER BY
            ticket_reduction_percent DESC,
            csat_change DESC;
        """
    )


def get_report_files(report_dir: Path = Path("reports")) -> list[Path]:
    if not report_dir.exists():
        return []

    return sorted(report_dir.glob("*.md"), reverse=True)


def read_report(path: Path) -> str:
    return path.read_text(encoding="utf-8")
