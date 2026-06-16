from __future__ import annotations

import os
import sys
from dataclasses import dataclass

import psycopg
from dotenv import load_dotenv

EXPECTED_TABLES = [
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


@dataclass(frozen=True)
class DatabaseCheckResult:
    database_name: str
    database_user: str
    postgres_version: str
    existing_tables: list[str]

    @property
    def missing_tables(self) -> list[str]:
        return [table for table in EXPECTED_TABLES if table not in self.existing_tables]


def get_database_url() -> str:
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is not set. Create .env from .env.example first.")

    return database_url


def run_database_check(database_url: str) -> DatabaseCheckResult:
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database(), current_user, version();")
            database_name, database_user, postgres_version = cur.fetchone()

            cur.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
                """
            )
            existing_tables = [row[0] for row in cur.fetchall()]

    return DatabaseCheckResult(
        database_name=database_name,
        database_user=database_user,
        postgres_version=postgres_version,
        existing_tables=existing_tables,
    )


def main() -> int:
    try:
        database_url = get_database_url()
        result = run_database_check(database_url)
    except Exception as exc:
        print("Database check failed.")
        print(f"Error: {exc}")
        return 1

    print("Database connection successful.")
    print(f"Database: {result.database_name}")
    print(f"User: {result.database_user}")
    print(f"PostgreSQL: {result.postgres_version.split(',')[0]}")

    if result.existing_tables:
        print("")
        print("Existing public tables:")
        for table in result.existing_tables:
            print(f"  - {table}")
    else:
        print("")
        print("No public tables found yet.")

    if result.missing_tables:
        print("")
        print("Schema status: incomplete")
        print("Missing expected tables:")
        for table in result.missing_tables:
            print(f"  - {table}")
    else:
        print("")
        print("Schema status: complete")
        print(f"Found all {len(EXPECTED_TABLES)} expected tables.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
