from __future__ import annotations

import argparse
import os
import sys

from agile_cx_roadmap.backlog.prioritization import prioritize_backlog
from dotenv import load_dotenv


def get_database_url() -> str:
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is missing. Create .env from .env.example.")

    return database_url


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate or refresh prioritized CX backlog items."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write generated backlog prioritization results to the database.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=15,
        help="Number of ranked backlog items to print.",
    )
    return parser.parse_args()


def print_ranked_items(items: list, limit: int, dry_run: bool) -> None:
    mode = "DRY RUN" if dry_run else "APPLIED"

    print("")
    print(f"Backlog prioritization engine completed. Mode: {mode}")
    print("")

    print(
        f"{'Rank':<5} "
        f"{'Action':<13} "
        f"{'Priority':>8} "
        f"{'RICE':>8} "
        f"{'Effort':>6} "
        f"{'Title'}"
    )
    print("-" * 110)

    for index, item in enumerate(items[:limit], start=1):
        print(
            f"{index:<5} "
            f"{item.action:<13} "
            f"{item.priority_score:>8.2f} "
            f"{item.rice_score:>8.2f} "
            f"{item.effort_points:>6} "
            f"{item.title}"
        )

    print("")
    print("Recommendation guide:")
    print("- Do now: high CX and strong RICE")
    print("- CX escalation priority")
    print("- Efficient product opportunity")
    print("- Plan into upcoming sprint")
    print("- Keep in backlog")


def main() -> int:
    args = parse_args()
    dry_run = not args.apply

    try:
        items = prioritize_backlog(
            database_url=get_database_url(),
            dry_run=dry_run,
        )
    except Exception as exc:
        print("Backlog generation failed.")
        print(f"Error: {exc}")
        return 1

    print_ranked_items(items, limit=args.limit, dry_run=dry_run)

    if dry_run:
        print("")
        print("No database changes were written.")
        print("Run with --apply to update backlog_items.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
