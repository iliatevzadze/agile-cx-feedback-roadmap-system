from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row


def get_database_url() -> str:
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is missing. Create .env from .env.example.")

    return database_url


def fetch_all(sql: str, params: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
    with psycopg.connect(get_database_url()) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params or ())
            rows = cur.fetchall()

    return [dict(row) for row in rows]


def fetch_one(sql: str, params: tuple[Any, ...] | None = None) -> dict[str, Any] | None:
    with psycopg.connect(get_database_url()) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params or ())
            row = cur.fetchone()

    return dict(row) if row else None


def get_report_files(report_dir: Path = Path("reports")) -> list[dict[str, Any]]:
    if not report_dir.exists():
        return []

    files = []

    for path in sorted(report_dir.glob("*.md"), reverse=True):
        files.append(
            {
                "filename": path.name,
                "path": str(path),
                "size_bytes": path.stat().st_size,
            }
        )

    return files
