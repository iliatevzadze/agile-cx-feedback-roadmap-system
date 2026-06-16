from __future__ import annotations

import argparse
import os
import sys

from agile_cx_roadmap.backlog.story_generator import generate_user_stories
from dotenv import load_dotenv


def get_database_url() -> str:
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is missing. Create .env from .env.example.")

    return database_url


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Agile user stories and acceptance criteria for backlog items."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write generated user stories and criteria to the database.",
    )
    parser.add_argument(
        "--backlog-id",
        type=int,
        default=None,
        help="Generate story details for one backlog item.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of backlog items to process when --backlog-id is not provided.",
    )
    return parser.parse_args()


def print_results(results: list, dry_run: bool) -> None:
    mode = "DRY RUN" if dry_run else "APPLIED"

    print("")
    print(f"User story generator completed. Mode: {mode}")
    print("")

    if not results:
        print("No backlog items found.")
        return

    print(
        f"{'ID':<5} "
        f"{'Action':<13} "
        f"{'Priority':>8} "
        f"{'RICE':>8} "
        f"{'Product Area':<35} "
        f"{'Title'}"
    )
    print("-" * 130)

    for item in results:
        print(
            f"{item.backlog_item_id:<5} "
            f"{item.action:<13} "
            f"{item.priority_score:>8.2f} "
            f"{item.rice_score:>8.2f} "
            f"{item.product_area:<35} "
            f"{item.title}"
        )

    print("")
    print("Preview user story:")
    print(results[0].user_story)

    if dry_run:
        print("")
        print("No database changes were written.")
        print("Run with --apply to update backlog_items.")


def main() -> int:
    args = parse_args()
    dry_run = not args.apply

    try:
        results = generate_user_stories(
            database_url=get_database_url(),
            dry_run=dry_run,
            backlog_item_id=args.backlog_id,
            limit=args.limit,
        )
    except Exception as exc:
        print("User story generation failed.")
        print(f"Error: {exc}")
        return 1

    print_results(results, dry_run=dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
