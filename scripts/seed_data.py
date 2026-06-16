from __future__ import annotations

import os
import random
import sys
from datetime import UTC, datetime, time, timedelta
from typing import Any

import psycopg
from dotenv import load_dotenv


def t(
    area: str,
    name: str,
    issue_type: str,
    severity: str,
    workaround: bool,
    effort: int,
    weight: int,
) -> dict[str, Any]:
    return {
        "area": area,
        "name": name,
        "description": f"Recurring customer feedback about: {name}.",
        "issue_type": issue_type,
        "severity": severity,
        "workaround": workaround,
        "effort": effort,
        "weight": weight,
    }


PRODUCT_AREAS = [
    ("Authentication and Account Access", "Identity Platform"),
    ("Billing and Subscription", "Revenue Operations"),
    ("AI Conversation Quality", "AI Product Team"),
    ("Mobile App Performance", "Mobile Engineering"),
    ("Speech Recognition", "AI Speech Team"),
    ("Learning Progress Tracking", "Learning Experience"),
    ("Admin Dashboard", "B2B Platform"),
    ("Notifications", "Lifecycle Platform"),
]

THEMES = [
    t("Authentication and Account Access", "Password reset emails not arriving", "account_access", "sev_2_high", False, 5, 9),  # noqa: E501
    t("Authentication and Account Access", "SSO login fails for invited learners", "bug", "sev_1_critical", False, 8, 6),  # noqa: E501
    t("Authentication and Account Access", "Session expires during long lessons", "bug", "sev_2_high", True, 5, 5),  # noqa: E501
    t("Authentication and Account Access", "Account verification link expires too quickly", "account_access", "sev_3_medium", True, 3, 4),  # noqa: E501
    t("Billing and Subscription", "Subscription cancellation unclear", "billing", "sev_2_high", True, 3, 8),  # noqa: E501
    t("Billing and Subscription", "Invoice download missing company details", "feature_request", "sev_3_medium", True, 5, 5),  # noqa: E501
    t("Billing and Subscription", "Renewal reminder arrives too late", "billing", "sev_3_medium", True, 3, 4),  # noqa: E501
    t("Billing and Subscription", "Plan upgrade fails after payment", "bug", "sev_1_critical", False, 8, 5),  # noqa: E501
    t("AI Conversation Quality", "AI tutor gives repetitive answers", "data_quality", "sev_2_high", False, 8, 10),  # noqa: E501
    t("AI Conversation Quality", "AI tutor correction tone feels too harsh", "data_quality", "sev_3_medium", True, 5, 5),  # noqa: E501
    t("AI Conversation Quality", "AI tutor misunderstands beginner prompts", "bug", "sev_2_high", False, 8, 7),  # noqa: E501
    t("AI Conversation Quality", "Conversation history context is lost", "bug", "sev_2_high", False, 13, 6),  # noqa: E501
    t("Mobile App Performance", "Mobile app freezes during lessons", "performance", "sev_1_critical", False, 8, 8),  # noqa: E501
    t("Mobile App Performance", "Lesson loading time is slow on Android", "performance", "sev_2_high", True, 5, 6),  # noqa: E501
    t("Mobile App Performance", "App crashes after microphone permission prompt", "bug", "sev_1_critical", False, 5, 5),  # noqa: E501
    t("Mobile App Performance", "Offline lesson mode is unreliable", "bug", "sev_2_high", True, 8, 4),  # noqa: E501
    t("Speech Recognition", "Speech recognition fails in noisy environments", "data_quality", "sev_2_high", True, 13, 9),  # noqa: E501
    t("Speech Recognition", "Pronunciation score feels inconsistent", "data_quality", "sev_2_high", False, 8, 7),  # noqa: E501
    t("Speech Recognition", "Microphone calibration is missing", "feature_request", "sev_3_medium", True, 5, 5),  # noqa: E501
    t("Speech Recognition", "Speech feedback takes too long", "performance", "sev_3_medium", True, 5, 4),  # noqa: E501
    t("Learning Progress Tracking", "Progress streak resets incorrectly", "bug", "sev_2_high", False, 5, 8),  # noqa: E501
    t("Learning Progress Tracking", "Completed lessons appear unfinished", "bug", "sev_2_high", True, 5, 5),  # noqa: E501
    t("Learning Progress Tracking", "Weekly progress email has wrong totals", "data_quality", "sev_3_medium", True, 3, 4),  # noqa: E501
    t("Learning Progress Tracking", "Team progress report misses inactive learners", "feature_request", "sev_3_medium", True, 5, 4),  # noqa: E501
    t("Admin Dashboard", "Admin dashboard export missing filters", "feature_request", "sev_3_medium", True, 5, 7),  # noqa: E501
    t("Admin Dashboard", "Bulk invite status is unclear", "feature_request", "sev_3_medium", True, 3, 5),  # noqa: E501
    t("Admin Dashboard", "Role permissions are too limited", "feature_request", "sev_2_high", True, 8, 5),  # noqa: E501
    t("Admin Dashboard", "Dashboard analytics load slowly", "performance", "sev_2_high", True, 8, 6),  # noqa: E501
    t("Notifications", "Notifications arrive too late", "bug", "sev_3_medium", True, 3, 7),
    t("Notifications", "Reminder preferences are ignored", "bug", "sev_2_high", False, 5, 5),
    t("Notifications", "Push notifications missing on Android", "bug", "sev_2_high", True, 5, 6),
    t("Notifications", "In-app notification copy is unclear", "feature_request", "sev_4_low", True, 2, 3),  # noqa: E501
]

TABLES = [
    "customers",
    "product_areas",
    "support_tickets",
    "feedback_items",
    "feedback_themes",
    "backlog_items",
    "backlog_evidence",
    "sprints",
    "sprint_items",
    "retro_items",
    "release_impact",
]

SEVERITY_SCORE = {
    "sev_1_critical": 100,
    "sev_2_high": 75,
    "sev_3_medium": 45,
    "sev_4_low": 20,
}


def get_database_url() -> str:
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is missing. Create .env from .env.example.")
    return database_url


def insert_row(cur: psycopg.Cursor, table: str, data: dict[str, Any], id_column: str) -> int:
    columns = list(data)
    column_sql = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(columns))
    query = f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders}) RETURNING {id_column};"
    cur.execute(query, tuple(data.values()))
    return cur.fetchone()[0]


def reset_database(cur: psycopg.Cursor) -> None:
    cur.execute(
        """
        TRUNCATE TABLE
            release_impact,
            retro_items,
            sprint_items,
            sprints,
            backlog_evidence,
            backlog_items,
            feedback_themes,
            feedback_items,
            support_tickets,
            product_areas,
            customers
        RESTART IDENTITY CASCADE;
        """
    )


def company_name(rng: random.Random, index: int) -> str:
    prefixes = ["Nova", "Bright", "Atlas", "Prime", "Cloud", "Global", "Future", "Blue"]
    roots = ["Lingua", "Academy", "Learn", "Skills", "Fluent", "Campus", "Mentor", "Path"]
    suffixes = ["Labs", "Group", "Education", "Systems", "Hub", "Network"]
    return f"{rng.choice(prefixes)}{rng.choice(roots)} {rng.choice(suffixes)} {index:02d}"


def plan_for_segment(rng: random.Random, segment: str) -> str:
    if segment == "Enterprise":
        return rng.choice(["Business", "Enterprise", "Enterprise"])
    if segment == "Mid-Market":
        return rng.choice(["Growth", "Business", "Business"])
    return rng.choice(["Starter", "Growth", "Business"])


def arr_for_plan(rng: random.Random, plan: str) -> float:
    ranges = {
        "Starter": (600, 2400),
        "Growth": (2500, 9000),
        "Business": (9000, 35000),
        "Enterprise": (35000, 120000),
    }
    low, high = ranges[plan]
    return round(rng.uniform(low, high), 2)


def priority_for_severity(severity: str) -> str:
    if severity == "sev_1_critical":
        return "urgent"
    if severity == "sev_2_high":
        return "high"
    if severity == "sev_3_medium":
        return "medium"
    return "low"


def csat_for_ticket(rng: random.Random, severity: str, sla_breached: bool) -> int:
    options = {
        "sev_1_critical": [1, 2, 2, 3],
        "sev_2_high": [2, 3, 3, 4],
        "sev_3_medium": [3, 4, 4, 5],
        "sev_4_low": [4, 4, 5, 5],
    }
    score = rng.choice(options[severity])
    return max(1, score - 1) if sla_breached else score


def feedback_type(issue_type: str) -> str:
    if issue_type == "feature_request":
        return "feature_request"
    if issue_type in {"billing", "account_access"}:
        return "support_ticket"
    if issue_type in {"data_quality", "performance"}:
        return "csat_comment"
    return "escalation"


def impact_level(severity: str) -> str:
    if severity == "sev_1_critical":
        return "critical"
    if severity == "sev_2_high":
        return "high"
    if severity == "sev_3_medium":
        return "medium"
    return "low"


def create_product_areas(cur: psycopg.Cursor) -> dict[str, int]:
    ids = {}
    for name, owner_team in PRODUCT_AREAS:
        ids[name] = insert_row(
            cur,
            "product_areas",
            {
                "name": name,
                "owner_team": owner_team,
                "description": f"{name} owned by {owner_team}.",
            },
            "product_area_id",
        )
    return ids


def create_customers(cur: psycopg.Cursor, rng: random.Random) -> list[dict[str, Any]]:
    customers = []
    for index in range(1, 61):
        segment = rng.choices(["SMB", "Mid-Market", "Enterprise"], weights=[45, 35, 20], k=1)[0]
        plan = plan_for_segment(rng, segment)
        customer = {
            "company_name": company_name(rng, index),
            "segment": segment,
            "plan": plan,
            "arr_value": arr_for_plan(rng, plan),
            "health_score": rng.randint(35, 96),
            "created_at": datetime.now(UTC) - timedelta(days=rng.randint(90, 900)),
        }
        customer["customer_id"] = insert_row(cur, "customers", customer, "customer_id")
        customers.append(customer)
    return customers


def create_tickets(
    cur: psycopg.Cursor,
    rng: random.Random,
    customers: list[dict[str, Any]],
    product_area_ids: dict[str, int],
) -> list[dict[str, Any]]:
    tickets = []
    theme_weights = [item["weight"] for item in THEMES]
    channels = ["email", "chat", "web_form", "phone", "in_app"]

    for index in range(1, 1201):
        selected_theme = rng.choices(THEMES, weights=theme_weights, k=1)[0]
        customer = rng.choice(customers)
        created_at = datetime.now(UTC) - timedelta(
            days=rng.randint(1, 180),
            hours=rng.randint(0, 23),
            minutes=rng.randint(0, 59),
        )
        sla_probability = {
            "sev_1_critical": 0.42,
            "sev_2_high": 0.28,
            "sev_3_medium": 0.14,
            "sev_4_low": 0.05,
        }[selected_theme["severity"]]
        sla_breached = rng.random() < sla_probability
        response_minutes = rng.randint(5, 90)
        if sla_breached:
            response_minutes += rng.randint(120, 480)

        status = rng.choices(
            ["solved", "closed", "pending", "open"],
            weights=[55, 25, 12, 8],
            k=1,
        )[0]
        resolved_at = None
        if status in {"solved", "closed"}:
            resolved_at = created_at + timedelta(hours=rng.randint(2, 96))

        escalation_flag = rng.random() < {
            "sev_1_critical": 0.38,
            "sev_2_high": 0.22,
            "sev_3_medium": 0.09,
            "sev_4_low": 0.03,
        }[selected_theme["severity"]]
        churn_risk_flag = (
            customer["segment"] in {"Mid-Market", "Enterprise"}
            and selected_theme["severity"] in {"sev_1_critical", "sev_2_high"}
            and rng.random() < 0.16
        )
        csat = csat_for_ticket(rng, selected_theme["severity"], sla_breached)
        subject = f"{selected_theme['name']} - customer report #{index}"
        product_area_id = product_area_ids[selected_theme["area"]]
        ticket_id = insert_row(
            cur,
            "support_tickets",
            {
                "external_ticket_id": f"CX-{index:05d}",
                "customer_id": customer["customer_id"],
                "product_area_id": product_area_id,
                "channel": rng.choice(channels),
                "priority": priority_for_severity(selected_theme["severity"]),
                "status": status,
                "issue_type": selected_theme["issue_type"],
                "severity": selected_theme["severity"],
                "subject": subject,
                "description": (
                    f"{customer['company_name']} reported '{selected_theme['name']}'. "
                    "This case is tagged as recurring CX feedback for product review."
                ),
                "created_at": created_at,
                "first_response_at": created_at + timedelta(minutes=response_minutes),
                "resolved_at": resolved_at,
                "csat_score": csat,
                "sla_breached": sla_breached,
                "escalation_flag": escalation_flag,
                "churn_risk_flag": churn_risk_flag,
            },
            "ticket_id",
        )
        tickets.append(
            {
                "ticket_id": ticket_id,
                "customer_id": customer["customer_id"],
                "customer_arr": customer["arr_value"],
                "product_area_id": product_area_id,
                "theme": selected_theme,
                "subject": subject,
                "created_at": created_at,
                "csat": csat,
                "sla_breached": sla_breached,
                "escalation_flag": escalation_flag,
                "churn_risk_flag": churn_risk_flag,
            }
        )
    return tickets


def create_feedback(
    cur: psycopg.Cursor,
    rng: random.Random,
    tickets: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    feedback = []
    sources = ["zendesk", "intercom", "hubspot", "salesforce", "manual_import", "in_app_survey"]

    for ticket in rng.sample(tickets, 320):
        sentiment = "negative" if ticket["csat"] <= 3 else rng.choice(["neutral", "positive"])
        raw_text = (
            f"Customer feedback theme: {ticket['theme']['name']}. "
            "This creates avoidable support contact and product friction."
        )
        feedback_id = insert_row(
            cur,
            "feedback_items",
            {
                "customer_id": ticket["customer_id"],
                "ticket_id": ticket["ticket_id"],
                "product_area_id": ticket["product_area_id"],
                "feedback_type": feedback_type(ticket["theme"]["issue_type"]),
                "source": rng.choice(sources),
                "raw_text": raw_text,
                "sentiment": sentiment,
                "impact_level": impact_level(ticket["theme"]["severity"]),
                "created_at": ticket["created_at"] + timedelta(days=rng.randint(0, 5)),
            },
            "feedback_id",
        )
        feedback.append({**ticket, "feedback_id": feedback_id, "raw_text": raw_text})
    return feedback


def summarize_tickets(tickets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary = []
    for item in THEMES:
        related = [ticket for ticket in tickets if ticket["theme"]["name"] == item["name"]]
        customer_ids = {ticket["customer_id"] for ticket in related}
        arr_by_customer = {ticket["customer_id"]: ticket["customer_arr"] for ticket in related}
        csat_scores = [ticket["csat"] for ticket in related]
        summary.append(
            {
                "theme": item,
                "tickets": related,
                "frequency": len(related),
                "avg_csat": round(sum(csat_scores) / len(csat_scores), 2),
                "affected_customers": len(customer_ids),
                "affected_arr": round(sum(arr_by_customer.values()), 2),
                "escalations": sum(int(ticket["escalation_flag"]) for ticket in related),
                "sla_breaches": sum(int(ticket["sla_breached"]) for ticket in related),
                "churn_risks": sum(int(ticket["churn_risk_flag"]) for ticket in related),
            }
        )
    return summary


def create_feedback_themes(
    cur: psycopg.Cursor,
    summaries: list[dict[str, Any]],
    product_area_ids: dict[str, int],
) -> list[dict[str, Any]]:
    themes = []
    for item in summaries:
        selected_theme = item["theme"]
        product_area_id = product_area_ids[selected_theme["area"]]
        theme_id = insert_row(
            cur,
            "feedback_themes",
            {
                "product_area_id": product_area_id,
                "theme_name": selected_theme["name"],
                "theme_description": selected_theme["description"],
                "frequency_count": item["frequency"],
                "avg_csat": item["avg_csat"],
                "affected_customers": item["affected_customers"],
                "affected_arr": item["affected_arr"],
                "escalation_count": item["escalations"],
                "sla_breach_count": item["sla_breaches"],
                "churn_risk_count": item["churn_risks"],
            },
            "theme_id",
        )
        themes.append({**item, "theme_id": theme_id, "product_area_id": product_area_id})
    return themes


def score_theme(item: dict[str, Any]) -> dict[str, float]:
    severity = SEVERITY_SCORE[item["theme"]["severity"]]
    frequency = min((item["frequency"] / 80) * 100, 100)
    customer = min((item["affected_customers"] / 35) * 100, 100)
    revenue = min((item["affected_arr"] / 350000) * 100, 100)
    sla = min((item["sla_breaches"] / 35) * 100, 100)
    csat = min(((5 - item["avg_csat"]) / 4) * 100, 100)
    churn = min((item["churn_risks"] / 12) * 100, 100)
    workaround = 35 if item["theme"]["workaround"] else 90
    priority = (
        severity * 0.20
        + frequency * 0.20
        + customer * 0.15
        + revenue * 0.15
        + sla * 0.10
        + csat * 0.10
        + churn * 0.05
        + workaround * 0.05
    )
    rice_impact = round(severity / 25, 2)
    rice_confidence = 0.85 if item["frequency"] >= 25 else 0.70
    rice_score = (
        item["affected_customers"]
        * rice_impact
        * rice_confidence
        / item["theme"]["effort"]
    )
    return {
        "priority_score": round(priority, 2),
        "severity_score": round(severity, 2),
        "frequency_score": round(frequency, 2),
        "revenue_impact_score": round(revenue, 2),
        "customer_impact_score": round(customer, 2),
        "sla_risk_score": round(sla, 2),
        "csat_impact_score": round(csat, 2),
        "churn_risk_score": round(churn, 2),
        "workaround_score": round(workaround, 2),
        "rice_reach": round(item["affected_customers"], 2),
        "rice_impact": rice_impact,
        "rice_confidence": rice_confidence,
        "rice_effort": round(item["theme"]["effort"], 2),
        "rice_score": round(rice_score, 2),
    }


def backlog_text(item: dict[str, Any]) -> dict[str, str]:
    name = item["theme"]["name"]
    title = f"Improve: {name}"
    return {
        "title": title,
        "problem_statement": (
            f"Customers repeatedly report '{name}', creating {item['frequency']} tickets, "
            f"affecting {item['affected_customers']} customers "
            f"and ${item['affected_arr']:,.2f} ARR."
        ),
        "user_story": (
            f"As a learner or admin, I want the product to resolve '{name}' so that "
            "I can use the platform without contacting support."
        ),
        "acceptance_criteria": "\n".join(
            [
                f"- Product behavior related to '{name}' is improved.",
                "- Support can identify whether the fix is active.",
                "- Customer-facing messaging is clear.",
                "- Relevant product events are logged.",
                "- Post-release ticket volume is measured.",
            ]
        ),
        "definition_of_ready": "\n".join(
            [
                "- Customer evidence is linked.",
                "- CX priority score and RICE score are calculated.",
                "- Product area owner is identified.",
                "- Acceptance criteria are clear.",
                "- Effort estimate is added.",
            ]
        ),
        "definition_of_done": "\n".join(
            [
                "- Implementation is complete.",
                "- QA checks pass.",
                "- Support team receives release note.",
                "- Help Center or SOP is updated if needed.",
                "- Post-release support impact is measured.",
            ]
        ),
    }


def create_backlog(cur: psycopg.Cursor, themes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    backlog = []
    for item in themes:
        scores = score_theme(item)
        texts = backlog_text(item)
        status = "ready" if scores["priority_score"] >= 62 else "backlog"
        backlog_item = {
            "theme_id": item["theme_id"],
            "product_area_id": item["product_area_id"],
            **texts,
            **scores,
            "effort_points": item["theme"]["effort"],
            "status": status,
        }
        backlog_id = insert_row(cur, "backlog_items", backlog_item, "backlog_item_id")
        backlog.append({**item, **scores, "backlog_item_id": backlog_id, "status": status})
    return backlog


def create_evidence(
    cur: psycopg.Cursor,
    backlog: list[dict[str, Any]],
    feedback: list[dict[str, Any]],
) -> None:
    for item in backlog:
        for ticket in item["tickets"][:3]:
            insert_row(
                cur,
                "backlog_evidence",
                {
                    "backlog_item_id": item["backlog_item_id"],
                    "ticket_id": ticket["ticket_id"],
                    "evidence_type": "support_ticket",
                    "evidence_text": ticket["subject"],
                },
                "evidence_id",
            )

        related_feedback = [
            row for row in feedback if row["theme"]["name"] == item["theme"]["name"]
        ]
        for row in related_feedback[:2]:
            insert_row(
                cur,
                "backlog_evidence",
                {
                    "backlog_item_id": item["backlog_item_id"],
                    "feedback_id": row["feedback_id"],
                    "evidence_type": "customer_feedback",
                    "evidence_text": row["raw_text"],
                },
                "evidence_id",
            )


def create_sprints(cur: psycopg.Cursor, backlog: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sprint_configs = [
        ("Sprint 1 - Access and Billing Reliability", 34, "completed"),
        ("Sprint 2 - AI Learning Quality", 36, "completed"),
        ("Sprint 3 - Mobile and Speech Stability", 32, "completed"),
        ("Sprint 4 - Admin Visibility and Notifications", 30, "active"),
    ]
    sorted_items = sorted(backlog, key=lambda row: row["priority_score"], reverse=True)
    assigned_ids: set[int] = set()
    base_date = datetime.now(UTC).date() - timedelta(days=56)
    sprints = []

    for index, (name, capacity, sprint_status) in enumerate(sprint_configs):
        selected = []
        committed = 0
        for item in sorted_items:
            if item["backlog_item_id"] in assigned_ids:
                continue
            if committed + item["theme"]["effort"] <= capacity:
                selected.append(item)
                assigned_ids.add(item["backlog_item_id"])
                committed += item["theme"]["effort"]
            if committed >= capacity - 3:
                break

        completed = 0
        planned_statuses = []
        for item_index, item in enumerate(selected):
            if sprint_status == "completed":
                item_status = "released" if item_index % 4 != 0 else "done"
            else:
                item_status = ["in_progress", "qa", "to_do", "blocked"][item_index % 4]
            completed += item["theme"]["effort"] if item_status in {"done", "released"} else 0
            planned_statuses.append((item, item_status))

        start_date = base_date + timedelta(days=index * 14)
        sprint_id = insert_row(
            cur,
            "sprints",
            {
                "sprint_name": name,
                "sprint_goal": "Reduce high-impact customer friction using CX evidence.",
                "start_date": start_date,
                "end_date": start_date + timedelta(days=13),
                "capacity_points": capacity,
                "committed_points": committed,
                "completed_points": completed,
                "status": sprint_status,
            },
            "sprint_id",
        )

        for item, item_status in planned_statuses:
            started_at = datetime.combine(start_date, time.min, tzinfo=UTC)
            completed_at = None
            if item_status in {"done", "released"}:
                completed_at = started_at + timedelta(days=10)
            blocked = item_status == "blocked"
            insert_row(
                cur,
                "sprint_items",
                {
                    "sprint_id": sprint_id,
                    "backlog_item_id": item["backlog_item_id"],
                    "status": item_status,
                    "story_points": item["theme"]["effort"],
                    "started_at": started_at,
                    "completed_at": completed_at,
                    "blocked_flag": blocked,
                    "blocker_reason": "Waiting for Engineering investigation." if blocked else None,
                },
                "sprint_item_id",
            )
            item["status"] = item_status
            cur.execute(
                "UPDATE backlog_items SET status = %s WHERE backlog_item_id = %s;",
                (item_status, item["backlog_item_id"]),
            )
        sprints.append({"sprint_id": sprint_id, "name": name, "items": selected})
    return sprints


def create_retros(cur: psycopg.Cursor, sprints: list[dict[str, Any]]) -> None:
    rows = [
        ("went_well", "Support evidence made product priorities clearer.", "CX Ops Lead", "done"),
        ("did_not_work", "Some items needed stronger discovery notes.", "Product Manager", "open"),
        (
            "blocker",
            "A few bugs required deeper reproduction steps.",
            "Engineering Lead",
            "in_progress",
        ),
        ("process_improvement", "Add a Definition of Ready check.", "Scrum Master", "open"),
    ]
    for sprint in sprints:
        for category, description, owner, status in rows:
            insert_row(
                cur,
                "retro_items",
                {
                    "sprint_id": sprint["sprint_id"],
                    "category": category,
                    "description": description,
                    "action_owner": owner,
                    "action_status": status,
                },
                "retro_item_id",
            )


def create_release_impact(cur: psycopg.Cursor, backlog: list[dict[str, Any]]) -> None:
    for item in sorted(backlog, key=lambda row: row["priority_score"], reverse=True)[:10]:
        before_volume = max(10, int(item["frequency"] / 2))
        after_volume = max(1, int(before_volume * 0.58))
        before_csat = item["avg_csat"] or 3.2
        before_sla_rate = min(100, round((item["sla_breaches"] / before_volume) * 100, 2))
        insert_row(
            cur,
            "release_impact",
            {
                "backlog_item_id": item["backlog_item_id"],
                "product_area_id": item["product_area_id"],
                "before_ticket_volume": before_volume,
                "after_ticket_volume": after_volume,
                "before_avg_csat": before_csat,
                "after_avg_csat": min(5.0, round(before_csat + 0.35, 2)),
                "before_sla_breach_rate": before_sla_rate,
                "after_sla_breach_rate": max(0, round(before_sla_rate * 0.62, 2)),
                "measured_at": datetime.now(UTC),
            },
            "release_impact_id",
        )


def row_counts(cur: psycopg.Cursor) -> dict[str, int]:
    counts = {}
    for table in TABLES:
        cur.execute(f"SELECT COUNT(*) FROM {table};")
        counts[table] = cur.fetchone()[0]
    return counts


def print_counts(counts: dict[str, int]) -> None:
    print("")
    print("Seed data created successfully.")
    print("")
    print("Row counts:")
    for table, count in counts.items():
        print(f"  - {table}: {count}")


def seed_database() -> None:
    rng = random.Random(42)

    with psycopg.connect(get_database_url()) as conn:
        with conn.cursor() as cur:
            reset_database(cur)
            product_area_ids = create_product_areas(cur)
            customers = create_customers(cur, rng)
            tickets = create_tickets(cur, rng, customers, product_area_ids)
            feedback = create_feedback(cur, rng, tickets)
            themes = create_feedback_themes(cur, summarize_tickets(tickets), product_area_ids)
            backlog = create_backlog(cur, themes)
            create_evidence(cur, backlog, feedback)
            sprints = create_sprints(cur, backlog)
            create_retros(cur, sprints)
            create_release_impact(cur, backlog)
            counts = row_counts(cur)
        conn.commit()

    print_counts(counts)


def main() -> int:
    try:
        seed_database()
    except Exception as exc:
        print("Seed data generation failed.")
        print(f"Error: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
