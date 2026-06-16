from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import psycopg
from psycopg.rows import dict_row


@dataclass(frozen=True)
class BacklogStoryContext:
    backlog_item_id: int
    title: str
    product_area: str
    owner_team: str
    theme_name: str
    theme_description: str
    priority_score: float
    rice_score: float
    effort_points: int
    frequency_count: int
    affected_customers: int
    affected_arr: float
    avg_csat: float
    escalation_count: int
    sla_breach_count: int
    churn_risk_count: int
    evidence_examples: list[str]


@dataclass(frozen=True)
class GeneratedStory:
    backlog_item_id: int
    title: str
    problem_statement: str
    user_story: str
    acceptance_criteria: str
    definition_of_ready: str
    definition_of_done: str


@dataclass(frozen=True)
class StoryGenerationResult:
    backlog_item_id: int
    title: str
    product_area: str
    priority_score: float
    rice_score: float
    action: str
    user_story: str


def to_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def money(value: float) -> str:
    return f"${value:,.2f}"


def actor_for_product_area(product_area: str) -> str:
    actors = {
        "Authentication and Account Access": "returning learner or invited team member",
        "Billing and Subscription": "billing admin",
        "AI Conversation Quality": "language learner",
        "Mobile App Performance": "mobile learner",
        "Speech Recognition": "learner practicing pronunciation",
        "Learning Progress Tracking": "learner or team admin",
        "Admin Dashboard": "team admin",
        "Notifications": "learner managing study reminders",
    }
    return actors.get(product_area, "customer")


def value_outcome_for_product_area(product_area: str) -> str:
    outcomes = {
        "Authentication and Account Access": "access my account without contacting support",
        "Billing and Subscription": "manage subscription and billing tasks confidently",
        "AI Conversation Quality": "receive useful learning guidance from the AI tutor",
        "Mobile App Performance": "complete lessons without app interruptions",
        "Speech Recognition": "receive reliable pronunciation feedback",
        "Learning Progress Tracking": "trust that my learning progress is accurate",
        "Admin Dashboard": "manage learners and reporting without manual workarounds",
        "Notifications": "receive timely reminders that match my preferences",
    }
    return outcomes.get(product_area, "complete my task successfully")


def product_area_acceptance_criteria(context: BacklogStoryContext) -> list[str]:
    theme = context.theme_name.lower()
    area = context.product_area

    if area == "Authentication and Account Access":
        return [
            "Users receive clear success or failure feedback after every access attempt.",
            "Support agents can see the latest account-access event status.",
            "Failed access events are logged with enough detail for troubleshooting.",
            "The flow prevents duplicate or conflicting user actions.",
        ]

    if area == "Billing and Subscription":
        return [
            "The billing action is clearly explained before the customer confirms it.",
            "The user sees a confirmation state after completing the billing action.",
            "Billing-related errors include plain-language recovery guidance.",
            "Support can verify the latest billing state without engineering help.",
        ]

    if area == "AI Conversation Quality":
        return [
            "The AI tutor response is relevant to the learner's current context.",
            "Repeated or low-value AI responses are reduced in the tested scenarios.",
            "The learner can continue the conversation without losing learning context.",
            "The system logs AI quality signals for later review.",
        ]

    if area == "Mobile App Performance":
        return [
            "The affected lesson flow completes without freezing or crashing.",
            "The app shows a recoverable state if network or device issues occur.",
            "Performance events are logged for support and engineering review.",
            "The fix is verified on Android test coverage.",
        ]

    if area == "Speech Recognition":
        return [
            "Speech input produces a clear result or a clear retry message.",
            "The user receives understandable feedback when recognition confidence is low.",
            "Speech recognition failures are logged with device and environment context.",
            "The pronunciation experience remains usable in common real-world conditions.",
        ]

    if area == "Learning Progress Tracking":
        return [
            "Progress updates are saved consistently after lesson completion.",
            "The user sees the same progress state after closing and reopening the app.",
            "Incorrect or missing progress states are logged for investigation.",
            "Support can explain progress status using visible account data.",
        ]

    if area == "Admin Dashboard":
        return [
            "Admins can complete the target workflow without manual exports or workarounds.",
            "Dashboard loading or reporting states are clear to the admin.",
            "Role and permission behavior is visible and predictable.",
            "Admin actions are auditable for support and operations review.",
        ]

    if area == "Notifications":
        return [
            "Notification timing respects the user's saved preferences.",
            "The user can clearly update or disable notification settings.",
            "Failed notification delivery events are logged.",
            "The notification copy explains the expected user action clearly.",
        ]

    if "export" in theme:
        return [
            "The export includes the filters selected by the user.",
            "The exported file matches the dashboard view.",
            "The user receives a clear message if export generation fails.",
        ]

    return [
        "The affected customer workflow is improved.",
        "The user receives clear feedback in success and failure states.",
        "Support can identify whether the fix is active.",
    ]


def generate_problem_statement(context: BacklogStoryContext) -> str:
    return (
        f"Customers repeatedly report '{context.theme_name}' in "
        f"{context.product_area}. The theme has generated "
        f"{context.frequency_count} support tickets, affected "
        f"{context.affected_customers} customers and represents "
        f"{money(context.affected_arr)} in affected ARR. Average CSAT is "
        f"{context.avg_csat:.2f}, with {context.escalation_count} escalations, "
        f"{context.sla_breach_count} SLA breaches and "
        f"{context.churn_risk_count} churn-risk flags. This makes the issue "
        "a strong candidate for product backlog prioritization."
    )


def generate_user_story(context: BacklogStoryContext) -> str:
    actor = actor_for_product_area(context.product_area)
    outcome = value_outcome_for_product_area(context.product_area)

    return (
        f"As a {actor}, I want the product to resolve "
        f"'{context.theme_name}' so that I can {outcome}."
    )


def generate_acceptance_criteria(context: BacklogStoryContext) -> str:
    criteria = [
        f"The issue '{context.theme_name}' is addressed in the affected workflow.",
        *product_area_acceptance_criteria(context),
        "The change is covered by QA test cases.",
        "Support-facing notes explain what changed and how to verify it.",
        "Post-release ticket volume and CSAT are measured after release.",
    ]

    unique_criteria = list(dict.fromkeys(criteria))
    return "\n".join(f"- {item}" for item in unique_criteria)


def generate_definition_of_ready(context: BacklogStoryContext) -> str:
    items = [
        "Customer evidence is linked to the backlog item.",
        "The product area and owner team are identified.",
        "CX priority score and RICE score are calculated.",
        "Problem statement is based on support volume, CSAT and customer impact.",
        "Acceptance criteria are testable.",
        "Effort points are estimated.",
        "Dependencies or known blockers are documented.",
    ]

    if context.evidence_examples:
        items.append("At least one support-ticket or feedback example is available.")

    return "\n".join(f"- {item}" for item in items)


def generate_definition_of_done(context: BacklogStoryContext) -> str:
    items = [
        "Implementation is complete.",
        "QA checks pass for the acceptance criteria.",
        "Relevant event logging or support visibility is available.",
        "Support team receives a short release note.",
        "Help Center or SOP content is updated if needed.",
        "Sprint review includes the customer problem solved.",
        "Post-release support impact is measured.",
    ]

    if context.priority_score >= 75:
        items.append("High-priority CX impact is reviewed with Product and Support leads.")

    return "\n".join(f"- {item}" for item in items)


def generate_story(context: BacklogStoryContext) -> GeneratedStory:
    return GeneratedStory(
        backlog_item_id=context.backlog_item_id,
        title=context.title,
        problem_statement=generate_problem_statement(context),
        user_story=generate_user_story(context),
        acceptance_criteria=generate_acceptance_criteria(context),
        definition_of_ready=generate_definition_of_ready(context),
        definition_of_done=generate_definition_of_done(context),
    )


def fetch_evidence_examples(
    conn: psycopg.Connection,
    backlog_item_id: int,
    limit: int = 5,
) -> list[str]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT evidence_text
            FROM backlog_evidence
            WHERE backlog_item_id = %s
            ORDER BY evidence_id
            LIMIT %s;
            """,
            (backlog_item_id, limit),
        )
        rows = cur.fetchall()

    return [str(row["evidence_text"]) for row in rows]


def fetch_backlog_contexts(
    conn: psycopg.Connection,
    backlog_item_id: int | None,
    limit: int | None,
) -> list[BacklogStoryContext]:
    params: list[Any] = []
    where_clause = ""

    if backlog_item_id is not None:
        where_clause = "WHERE bi.backlog_item_id = %s"
        params.append(backlog_item_id)

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
                pa.owner_team,
                ft.theme_name,
                ft.theme_description,
                bi.priority_score,
                bi.rice_score,
                bi.effort_points,
                ft.frequency_count,
                ft.affected_customers,
                ft.affected_arr,
                ft.avg_csat,
                ft.escalation_count,
                ft.sla_breach_count,
                ft.churn_risk_count
            FROM backlog_items bi
            JOIN feedback_themes ft
                ON bi.theme_id = ft.theme_id
            JOIN product_areas pa
                ON bi.product_area_id = pa.product_area_id
            {where_clause}
            ORDER BY bi.priority_score DESC, bi.rice_score DESC
            {limit_clause};
            """,
            params,
        )
        rows = cur.fetchall()

    contexts = []

    for row in rows:
        item_id = int(row["backlog_item_id"])
        contexts.append(
            BacklogStoryContext(
                backlog_item_id=item_id,
                title=str(row["title"]),
                product_area=str(row["product_area"]),
                owner_team=str(row["owner_team"]),
                theme_name=str(row["theme_name"]),
                theme_description=str(row["theme_description"]),
                priority_score=to_float(row["priority_score"]),
                rice_score=to_float(row["rice_score"]),
                effort_points=int(row["effort_points"]),
                frequency_count=int(row["frequency_count"]),
                affected_customers=int(row["affected_customers"]),
                affected_arr=to_float(row["affected_arr"]),
                avg_csat=to_float(row["avg_csat"]),
                escalation_count=int(row["escalation_count"]),
                sla_breach_count=int(row["sla_breach_count"]),
                churn_risk_count=int(row["churn_risk_count"]),
                evidence_examples=fetch_evidence_examples(conn, item_id),
            )
        )

    return contexts


def update_backlog_story(
    conn: psycopg.Connection,
    story: GeneratedStory,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE backlog_items
            SET
                problem_statement = %s,
                user_story = %s,
                acceptance_criteria = %s,
                definition_of_ready = %s,
                definition_of_done = %s
            WHERE backlog_item_id = %s;
            """,
            (
                story.problem_statement,
                story.user_story,
                story.acceptance_criteria,
                story.definition_of_ready,
                story.definition_of_done,
                story.backlog_item_id,
            ),
        )


def generate_user_stories(
    database_url: str,
    dry_run: bool,
    backlog_item_id: int | None = None,
    limit: int | None = None,
) -> list[StoryGenerationResult]:
    with psycopg.connect(database_url) as conn:
        contexts = fetch_backlog_contexts(
            conn=conn,
            backlog_item_id=backlog_item_id,
            limit=limit,
        )

        results = []

        for context in contexts:
            story = generate_story(context)

            if not dry_run:
                update_backlog_story(conn, story)

            results.append(
                StoryGenerationResult(
                    backlog_item_id=context.backlog_item_id,
                    title=context.title,
                    product_area=context.product_area,
                    priority_score=context.priority_score,
                    rice_score=context.rice_score,
                    action="would_update" if dry_run else "updated",
                    user_story=story.user_story,
                )
            )

        if dry_run:
            conn.rollback()
        else:
            conn.commit()

    return results
