from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import psycopg
from psycopg.rows import dict_row


@dataclass(frozen=True)
class ThemeMetrics:
    theme_id: int
    product_area_id: int
    product_area: str
    theme_name: str
    frequency_count: int
    avg_csat: float
    affected_customers: int
    affected_arr: float
    escalation_count: int
    sla_breach_count: int
    churn_risk_count: int
    existing_backlog_item_id: int | None
    existing_effort_points: int | None


@dataclass(frozen=True)
class ScoreBreakdown:
    priority_score: float
    severity_score: float
    frequency_score: float
    revenue_impact_score: float
    customer_impact_score: float
    sla_risk_score: float
    csat_impact_score: float
    churn_risk_score: float
    workaround_score: float
    effort_points: int
    rice_reach: float
    rice_impact: float
    rice_confidence: float
    rice_effort: float
    rice_score: float


@dataclass(frozen=True)
class BacklogText:
    title: str
    problem_statement: str
    user_story: str
    acceptance_criteria: str
    definition_of_ready: str
    definition_of_done: str


@dataclass(frozen=True)
class PrioritizedBacklogItem:
    backlog_item_id: int | None
    theme_id: int
    product_area: str
    title: str
    priority_score: float
    rice_score: float
    effort_points: int
    recommendation: str
    action: str


def to_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def percent_score(value: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return round(min((value / denominator) * 100, 100), 2)


def infer_severity_score(theme: ThemeMetrics) -> float:
    if theme.avg_csat <= 2.0:
        return 100.0
    if theme.sla_breach_count >= 15:
        return 100.0
    if theme.escalation_count >= 15:
        return 100.0
    if theme.avg_csat <= 3.0:
        return 75.0
    if theme.churn_risk_count >= 5:
        return 75.0
    if theme.frequency_count >= 25:
        return 45.0
    return 20.0


def infer_workaround_score(theme: ThemeMetrics) -> float:
    no_workaround_keywords = [
        "not arriving",
        "fails",
        "freezes",
        "crashes",
        "resets incorrectly",
        "ignored",
        "lost",
    ]

    theme_name = theme.theme_name.lower()

    if any(keyword in theme_name for keyword in no_workaround_keywords):
        return 90.0

    return 35.0


def infer_effort_points(theme: ThemeMetrics) -> int:
    if theme.existing_effort_points:
        return theme.existing_effort_points

    if theme.affected_customers >= 35 or theme.sla_breach_count >= 15:
        return 8

    if theme.frequency_count >= 30:
        return 5

    return 3


def confidence_score(theme: ThemeMetrics) -> float:
    if theme.frequency_count >= 50 and theme.affected_customers >= 30:
        return 0.90
    if theme.frequency_count >= 25:
        return 0.85
    return 0.70


def calculate_scores(theme: ThemeMetrics) -> ScoreBreakdown:
    severity_score = infer_severity_score(theme)
    workaround_score = infer_workaround_score(theme)
    effort_points = infer_effort_points(theme)

    frequency_score = percent_score(theme.frequency_count, 80)
    customer_impact_score = percent_score(theme.affected_customers, 35)
    revenue_impact_score = percent_score(theme.affected_arr, 350_000)
    sla_risk_score = percent_score(theme.sla_breach_count, 35)
    csat_impact_score = round(min(((5 - theme.avg_csat) / 4) * 100, 100), 2)
    churn_risk_score = percent_score(theme.churn_risk_count, 12)

    priority_score = round(
        severity_score * 0.20
        + frequency_score * 0.20
        + customer_impact_score * 0.15
        + revenue_impact_score * 0.15
        + sla_risk_score * 0.10
        + csat_impact_score * 0.10
        + churn_risk_score * 0.05
        + workaround_score * 0.05,
        2,
    )

    rice_reach = float(theme.affected_customers)
    rice_impact = round(severity_score / 25, 2)
    rice_confidence = confidence_score(theme)
    rice_effort = float(effort_points)
    rice_score = round(
        (rice_reach * rice_impact * rice_confidence) / rice_effort,
        2,
    )

    return ScoreBreakdown(
        priority_score=priority_score,
        severity_score=round(severity_score, 2),
        frequency_score=frequency_score,
        revenue_impact_score=revenue_impact_score,
        customer_impact_score=customer_impact_score,
        sla_risk_score=sla_risk_score,
        csat_impact_score=csat_impact_score,
        churn_risk_score=churn_risk_score,
        workaround_score=round(workaround_score, 2),
        effort_points=effort_points,
        rice_reach=rice_reach,
        rice_impact=rice_impact,
        rice_confidence=rice_confidence,
        rice_effort=rice_effort,
        rice_score=rice_score,
    )


def recommendation(scores: ScoreBreakdown) -> str:
    if scores.priority_score >= 75 and scores.rice_score >= 15:
        return "Do now: high CX and strong RICE"
    if scores.priority_score >= 75:
        return "CX escalation priority"
    if scores.rice_score >= 20:
        return "Efficient product opportunity"
    if scores.priority_score >= 60:
        return "Plan into upcoming sprint"
    return "Keep in backlog"


def generate_backlog_text(theme: ThemeMetrics) -> BacklogText:
    title = f"Improve: {theme.theme_name}"

    problem_statement = (
        f"Customers repeatedly report '{theme.theme_name}', creating "
        f"{theme.frequency_count} support tickets, affecting "
        f"{theme.affected_customers} customers and ${theme.affected_arr:,.2f} ARR. "
        f"The average CSAT for this theme is {theme.avg_csat:.2f}."
    )

    user_story = (
        f"As a learner or admin, I want the product to resolve "
        f"'{theme.theme_name}' so that I can use the platform without "
        "contacting support."
    )

    acceptance_criteria = "\n".join(
        [
            f"- Product behavior related to '{theme.theme_name}' is improved.",
            "- Support can identify whether the fix is active.",
            "- Customer-facing messaging is clear.",
            "- Relevant product events are logged.",
            "- Post-release ticket volume is measured.",
        ]
    )

    definition_of_ready = "\n".join(
        [
            "- Customer evidence is linked.",
            "- CX priority score and RICE score are calculated.",
            "- Product area owner is identified.",
            "- Acceptance criteria are clear.",
            "- Effort estimate is added.",
        ]
    )

    definition_of_done = "\n".join(
        [
            "- Implementation is complete.",
            "- QA checks pass.",
            "- Support team receives release note.",
            "- Help Center or SOP is updated if needed.",
            "- Post-release support impact is measured.",
        ]
    )

    return BacklogText(
        title=title,
        problem_statement=problem_statement,
        user_story=user_story,
        acceptance_criteria=acceptance_criteria,
        definition_of_ready=definition_of_ready,
        definition_of_done=definition_of_done,
    )


def fetch_theme_metrics(conn: psycopg.Connection) -> list[ThemeMetrics]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT
                ft.theme_id,
                ft.product_area_id,
                pa.name AS product_area,
                ft.theme_name,
                ft.frequency_count,
                ft.avg_csat,
                ft.affected_customers,
                ft.affected_arr,
                ft.escalation_count,
                ft.sla_breach_count,
                ft.churn_risk_count,
                bi.backlog_item_id AS existing_backlog_item_id,
                bi.effort_points AS existing_effort_points
            FROM feedback_themes ft
            JOIN product_areas pa
                ON ft.product_area_id = pa.product_area_id
            LEFT JOIN backlog_items bi
                ON ft.theme_id = bi.theme_id
            ORDER BY ft.theme_id;
            """
        )
        rows = cur.fetchall()

    return [
        ThemeMetrics(
            theme_id=int(row["theme_id"]),
            product_area_id=int(row["product_area_id"]),
            product_area=str(row["product_area"]),
            theme_name=str(row["theme_name"]),
            frequency_count=int(row["frequency_count"]),
            avg_csat=to_float(row["avg_csat"]),
            affected_customers=int(row["affected_customers"]),
            affected_arr=to_float(row["affected_arr"]),
            escalation_count=int(row["escalation_count"]),
            sla_breach_count=int(row["sla_breach_count"]),
            churn_risk_count=int(row["churn_risk_count"]),
            existing_backlog_item_id=row["existing_backlog_item_id"],
            existing_effort_points=row["existing_effort_points"],
        )
        for row in rows
    ]


def update_existing_backlog_item(
    conn: psycopg.Connection,
    backlog_item_id: int,
    theme: ThemeMetrics,
    scores: ScoreBreakdown,
    text: BacklogText,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE backlog_items
            SET
                product_area_id = %s,
                title = %s,
                problem_statement = %s,
                user_story = %s,
                acceptance_criteria = %s,
                definition_of_ready = %s,
                definition_of_done = %s,
                priority_score = %s,
                severity_score = %s,
                frequency_score = %s,
                revenue_impact_score = %s,
                customer_impact_score = %s,
                sla_risk_score = %s,
                csat_impact_score = %s,
                churn_risk_score = %s,
                workaround_score = %s,
                effort_points = %s,
                rice_reach = %s,
                rice_impact = %s,
                rice_confidence = %s,
                rice_effort = %s,
                rice_score = %s
            WHERE backlog_item_id = %s;
            """,
            (
                theme.product_area_id,
                text.title,
                text.problem_statement,
                text.user_story,
                text.acceptance_criteria,
                text.definition_of_ready,
                text.definition_of_done,
                scores.priority_score,
                scores.severity_score,
                scores.frequency_score,
                scores.revenue_impact_score,
                scores.customer_impact_score,
                scores.sla_risk_score,
                scores.csat_impact_score,
                scores.churn_risk_score,
                scores.workaround_score,
                scores.effort_points,
                scores.rice_reach,
                scores.rice_impact,
                scores.rice_confidence,
                scores.rice_effort,
                scores.rice_score,
                backlog_item_id,
            ),
        )


def insert_new_backlog_item(
    conn: psycopg.Connection,
    theme: ThemeMetrics,
    scores: ScoreBreakdown,
    text: BacklogText,
) -> int:
    status = "ready" if scores.priority_score >= 60 else "backlog"

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO backlog_items (
                theme_id,
                product_area_id,
                title,
                problem_statement,
                user_story,
                acceptance_criteria,
                definition_of_ready,
                definition_of_done,
                priority_score,
                severity_score,
                frequency_score,
                revenue_impact_score,
                customer_impact_score,
                sla_risk_score,
                csat_impact_score,
                churn_risk_score,
                workaround_score,
                effort_points,
                rice_reach,
                rice_impact,
                rice_confidence,
                rice_effort,
                rice_score,
                status
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING backlog_item_id;
            """,
            (
                theme.theme_id,
                theme.product_area_id,
                text.title,
                text.problem_statement,
                text.user_story,
                text.acceptance_criteria,
                text.definition_of_ready,
                text.definition_of_done,
                scores.priority_score,
                scores.severity_score,
                scores.frequency_score,
                scores.revenue_impact_score,
                scores.customer_impact_score,
                scores.sla_risk_score,
                scores.csat_impact_score,
                scores.churn_risk_score,
                scores.workaround_score,
                scores.effort_points,
                scores.rice_reach,
                scores.rice_impact,
                scores.rice_confidence,
                scores.rice_effort,
                scores.rice_score,
                status,
            ),
        )
        return int(cur.fetchone()[0])


def upsert_backlog_item(
    conn: psycopg.Connection,
    theme: ThemeMetrics,
    scores: ScoreBreakdown,
    text: BacklogText,
    dry_run: bool,
) -> PrioritizedBacklogItem:
    item_recommendation = recommendation(scores)

    if dry_run:
        action = "would_update" if theme.existing_backlog_item_id else "would_create"
        return PrioritizedBacklogItem(
            backlog_item_id=theme.existing_backlog_item_id,
            theme_id=theme.theme_id,
            product_area=theme.product_area,
            title=text.title,
            priority_score=scores.priority_score,
            rice_score=scores.rice_score,
            effort_points=scores.effort_points,
            recommendation=item_recommendation,
            action=action,
        )

    if theme.existing_backlog_item_id:
        backlog_item_id = int(theme.existing_backlog_item_id)
        update_existing_backlog_item(conn, backlog_item_id, theme, scores, text)
        action = "updated"
    else:
        backlog_item_id = insert_new_backlog_item(conn, theme, scores, text)
        action = "created"

    return PrioritizedBacklogItem(
        backlog_item_id=backlog_item_id,
        theme_id=theme.theme_id,
        product_area=theme.product_area,
        title=text.title,
        priority_score=scores.priority_score,
        rice_score=scores.rice_score,
        effort_points=scores.effort_points,
        recommendation=item_recommendation,
        action=action,
    )


def prioritize_backlog(
    database_url: str,
    dry_run: bool,
) -> list[PrioritizedBacklogItem]:
    with psycopg.connect(database_url) as conn:
        themes = fetch_theme_metrics(conn)
        prioritized_items = []

        for theme in themes:
            scores = calculate_scores(theme)
            text = generate_backlog_text(theme)
            item = upsert_backlog_item(
                conn=conn,
                theme=theme,
                scores=scores,
                text=text,
                dry_run=dry_run,
            )
            prioritized_items.append(item)

        if dry_run:
            conn.rollback()
        else:
            conn.commit()

    return sorted(
        prioritized_items,
        key=lambda row: (row.priority_score, row.rice_score),
        reverse=True,
    )
