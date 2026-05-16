#!/usr/bin/env python3
"""
Initialize SQLite database for boatrace-ai-free.

STEP 62

This script:
- reads db/schema.sql
- creates db/boatrace.sqlite3
- executes the schema
- verifies required tables and views
- runs foreign key check
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_SCHEMA_PATH = PROJECT_ROOT / "db" / "schema.sql"
DEFAULT_DB_PATH = PROJECT_ROOT / "db" / "boatrace.sqlite3"


REQUIRED_TABLES = {
    "venues",
    "races",
    "racers",
    "race_entries",
    "odds_snapshots",
    "prediction_runs",
    "predictions",
    "prediction_tickets",
    "race_results",
    "alert_events",
    "export_logs",
}

REQUIRED_VIEWS = {
    "v_race_overview",
    "v_prediction_ticket_results",
    "v_prediction_run_summary",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Initialize SQLite database from db/schema.sql."
    )

    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA_PATH,
        help="Path to schema.sql. Default: db/schema.sql",
    )

    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help="Path to SQLite database. Default: db/boatrace.sqlite3",
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing database before initialization.",
    )

    return parser.parse_args()


def print_list(title: str, values: Iterable[str]) -> None:
    print(f"\n{title}:")
    for value in sorted(values):
        print(f"  - {value}")


def fetch_object_names(conn: sqlite3.Connection, object_type: str) -> set[str]:
    rows = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = ?
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """,
        (object_type,),
    ).fetchall()

    return {row[0] for row in rows}


def validate_required_objects(
    existing_tables: set[str],
    existing_views: set[str],
) -> None:
    missing_tables = REQUIRED_TABLES - existing_tables
    missing_views = REQUIRED_VIEWS - existing_views

    if missing_tables:
        print_list("Missing tables", missing_tables)

    if missing_views:
        print_list("Missing views", missing_views)

    if missing_tables or missing_views:
        raise RuntimeError("Required database objects are missing.")


def run_foreign_key_check(conn: sqlite3.Connection) -> None:
    rows = conn.execute("PRAGMA foreign_key_check").fetchall()

    if rows:
        print("\nForeign key check: NG")
        for row in rows:
            print(row)
        raise RuntimeError("Foreign key check failed.")

    print("\nForeign key check: OK")


def initialize_database(schema_path: Path, db_path: Path, reset: bool = False) -> None:
    schema_path = schema_path.resolve()
    db_path = db_path.resolve()

    print(f"Schema file: {schema_path.relative_to(PROJECT_ROOT)}")
    print(f"Database file: {db_path.relative_to(PROJECT_ROOT)}")

    if not schema_path.exists():
      raise FileNotFoundError(f"Schema file not found: {schema_path}")

    db_path.parent.mkdir(parents=True, exist_ok=True)

    if reset and db_path.exists():
        print("\nReset enabled. Removing existing database...")
        db_path.unlink()

    print("\nCreating database...")
    conn = sqlite3.connect(db_path)

    try:
        conn.execute("PRAGMA foreign_keys = ON")

        schema_sql = schema_path.read_text(encoding="utf-8")

        print("Executing schema...")
        conn.executescript(schema_sql)

        print("Checking tables and views...")

        existing_tables = fetch_object_names(conn, "table")
        existing_views = fetch_object_names(conn, "view")

        print_list("Tables", existing_tables)
        print_list("Views", existing_views)

        validate_required_objects(existing_tables, existing_views)
        run_foreign_key_check(conn)

        conn.commit()

    finally:
        conn.close()

    print("\nSTEP 62 CHECK: OK")


def main() -> None:
    args = parse_args()

    initialize_database(
        schema_path=args.schema,
        db_path=args.db,
        reset=args.reset,
    )


if __name__ == "__main__":
    main()

