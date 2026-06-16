from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from agile_cx_roadmap.reports.sprint_report import generate_sprint_report
from dotenv import load_dotenv


def get_database_url() -> str:
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is missing. Create .env from .env.example.")

    return database_url


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a Markdown sprint review and retrospective report."
    )
    parser.add_argument(
        "--sprint-id",
        type=int,
        default=None,
        help="Sprint ID to report on. Defaults to the latest sprint.",
    )
    parser.add_argument(
        "--output-dir",
        default="reports",
        help="Directory where the Markdown report will be written.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        result = generate_sprint_report(
            database_url=get_database_url(),
            output_dir=Path(args.output_dir),
            sprint_id=args.sprint_id,
        )
    except Exception as exc:
        print("Sprint report generation failed.")
        print(f"Error: {exc}")
        return 1

    print("")
    print("Sprint review report generated successfully.")
    print("")
    print(f"Sprint ID: {result.sprint_id}")
    print(f"Sprint name: {result.sprint_name}")
    print(f"Items included: {result.item_count}")
    print(f"Committed points: {result.committed_points}")
    print(f"Completed points: {result.completed_points}")
    print(f"Completion rate: {result.completion_rate:.2f}%")
    print(f"Output file: {result.output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
