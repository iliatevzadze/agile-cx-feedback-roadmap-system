from __future__ import annotations

import argparse
import os
import sys
from datetime import date

from agile_cx_roadmap.sprints.planner import plan_sprint
from dotenv import load_dotenv


def get_database_url() -> str:
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is missing. Create .env from .env.example.")

    return database_url


def parse_start_date(value: str | None) -> date | None:
    if value is None:
        return None
    return date.fromisoformat(value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plan a sprint from prioritized CX backlog items."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Create the sprint and sprint item rows in the database.",
    )
    parser.add_argument(
        "--capacity",
        type=int,
        default=30,
        help="Sprint capacity in story points.",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=14,
        help="Sprint duration in days.",
    )
    parser.add_argument(
        "--start-date",
        default=None,
        help="Optional sprint start date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--candidate-limit",
        type=int,
        default=None,
        help="Optional number of backlog candidates to evaluate.",
    )
    return parser.parse_args()


def print_plan(plan, dry_run: bool) -> None:
    mode = "DRY RUN" if dry_run else "APPLIED"

    print("")
    print(f"Sprint planning engine completed. Mode: {mode}")
    print("")
    print(f"Action: {plan.action}")
    if plan.sprint_id is not None:
        print(f"Sprint ID: {plan.sprint_id}")
    print(f"Sprint name: {plan.sprint_name}")
    print(f"Start date: {plan.start_date}")
    print(f"End date: {plan.end_date}")
    print(f"Capacity points: {plan.capacity_points}")
    print(f"Committed points: {plan.committed_points}")
    print(f"Sprint goal: {plan.sprint_goal}")

    print("")
    print("Selected sprint items:")
    print(
        f"{'Order':<6} "
        f"{'ID':<5} "
        f"{'Points':>6} "
        f"{'Priority':>8} "
        f"{'RICE':>8} "
        f"{'Product Area':<35} "
        f"{'Title'}"
    )
    print("-" * 140)

    if not plan.selected_items:
        print("No backlog items fit the sprint capacity.")
    else:
        for item in plan.selected_items:
            print(
                f"{item.planned_order:<6} "
                f"{item.backlog_item_id:<5} "
                f"{item.effort_points:>6} "
                f"{item.priority_score:>8.2f} "
                f"{item.rice_score:>8.2f} "
                f"{item.product_area:<35} "
                f"{item.title}"
            )

    print("")
    print(f"Skipped items because of capacity: {len(plan.skipped_items)}")

    if dry_run:
        print("")
        print("No database changes were written.")
        print("Run with --apply to create the sprint.")


def main() -> int:
    args = parse_args()
    dry_run = not args.apply

    try:
        plan = plan_sprint(
            database_url=get_database_url(),
            dry_run=dry_run,
            capacity_points=args.capacity,
            duration_days=args.days,
            start_date_override=parse_start_date(args.start_date),
            candidate_limit=args.candidate_limit,
        )
    except Exception as exc:
        print("Sprint planning failed.")
        print(f"Error: {exc}")
        return 1

    print_plan(plan, dry_run=dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
