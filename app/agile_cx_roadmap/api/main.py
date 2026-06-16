from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Query

from agile_cx_roadmap.api.db import fetch_all, fetch_one, get_report_files

app = FastAPI(
    title="Agile CX Feedback-to-Roadmap API",
    description=(
        "Read API for a local CX Operations portfolio project that converts "
        "support feedback into prioritized backlog items, sprint plans and "
        "release impact reports."
    ),
    version="0.1.0",
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "Agile CX Feedback-to-Roadmap API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health() -> dict[str, Any]:
    row = fetch_one(
        """
        SELECT
            CURRENT_DATABASE() AS database,
            CURRENT_USER AS user_name,
            VERSION() AS postgres_version;
        """
    )

    if row is None:
        raise HTTPException(status_code=500, detail="Database health check failed.")

    return {
        "status": "ok",
        "database": row["database"],
        "user": row["user_name"],
        "postgres_version": row["postgres_version"],
    }


@app.get("/kpis")
def kpis() -> dict[str, Any]:
    row = fetch_one(
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

    if row is None:
        raise HTTPException(status_code=500, detail="KPI query failed.")

    return row


@app.get("/feedback-themes")
def feedback_themes(
    product_area: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict[str, Any]]:
    params: list[Any] = []
    where_clause = ""

    if product_area:
        where_clause = "WHERE pa.name = %s"
        params.append(product_area)

    params.append(limit)

    return fetch_all(
        f"""
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
        {where_clause}
        ORDER BY
            bi.priority_score DESC,
            ft.affected_arr DESC
        LIMIT %s;
        """,
        tuple(params),
    )


@app.get("/backlog")
def backlog(
    status: str | None = Query(default=None),
    min_priority: float = Query(default=0, ge=0, le=100),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict[str, Any]]:
    params: list[Any] = [min_priority]
    status_clause = ""

    if status:
        status_clause = "AND bi.status = %s"
        params.append(status)

    params.append(limit)

    return fetch_all(
        f"""
        SELECT
            bi.backlog_item_id,
            bi.title,
            pa.name AS product_area,
            bi.status,
            bi.effort_points,
            bi.priority_score,
            bi.rice_score,
            bi.problem_statement,
            bi.user_story,
            bi.acceptance_criteria,
            bi.definition_of_ready,
            bi.definition_of_done
        FROM backlog_items bi
        JOIN product_areas pa
            ON bi.product_area_id = pa.product_area_id
        WHERE bi.priority_score >= %s
        {status_clause}
        ORDER BY
            bi.priority_score DESC,
            bi.rice_score DESC,
            bi.effort_points ASC
        LIMIT %s;
        """,
        tuple(params),
    )


@app.get("/sprints")
def sprints() -> list[dict[str, Any]]:
    return fetch_all(
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


@app.get("/sprints/{sprint_id}")
def sprint_detail(sprint_id: int) -> dict[str, Any]:
    sprint = fetch_one(
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

    if sprint is None:
        raise HTTPException(status_code=404, detail=f"Sprint {sprint_id} not found.")

    items = fetch_all(
        """
        SELECT
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
        WHERE si.sprint_id = %s
        ORDER BY si.sprint_item_id;
        """,
        (sprint_id,),
    )

    sprint["items"] = items
    return sprint


@app.get("/release-impact")
def release_impact(limit: int = Query(default=50, ge=1, le=200)) -> list[dict[str, Any]]:
    return fetch_all(
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
            csat_change DESC
        LIMIT %s;
        """,
        (limit,),
    )


@app.get("/reports")
def reports() -> list[dict[str, Any]]:
    return get_report_files()
