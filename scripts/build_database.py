#!/usr/bin/env python3
import argparse
import sqlite3
import subprocess
import sys
from pathlib import Path


DB_PATH = Path("db/boatrace.sqlite3")
PYTHON = sys.executable


REQUIRED_TABLES = [
    "venues",
    "racers",
    "races",
    "race_entries",
    "odds_snapshots",
    "prediction_runs",
    "predictions",
    "prediction_tickets",
    "alert_events",
    "export_logs",
]


REQUIRED_COLUMNS = {
    "venues": [
        "id",
    ],
    "racers": [
        "id",
    ],
    "races": [
        "id",
    ],
    "race_entries": [
        "id",
    ],
    "odds_snapshots": [
        "id",
    ],
    "prediction_runs": [
        "id",
    ],
    "predictions": [
        "id",
    ],
    "prediction_tickets": [
        "id",
        "prediction_id",
        "bet_type",
        "combination",
        "odds",
        "expected_value",
    ],
    "alert_events": [
        "id",
    ],
}


def run(command: list[str]) -> None:
    print("")
    print("=" * 80)
    print("RUN:", " ".join(command))
    print("=" * 80)

    result = subprocess.run(command)

    if result.returncode != 0:
        raise SystemExit(
            f"Command failed with exit code {result.returncode}: {' '.join(command)}"
        )


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {row[1] for row in rows}


def table_count(conn: sqlite3.Connection, table: str) -> int:
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def validate_schema() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"Database file does not exist: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    print("")
    print("Database:", DB_PATH)
    print("SQLite version:", sqlite3.sqlite_version)

    missing_tables = []

    for table in REQUIRED_TABLES:
        if not table_exists(conn, table):
            missing_tables.append(table)

    if missing_tables:
        raise SystemExit(f"Missing required tables: {missing_tables}")

    print("")
    print("Required tables: OK")

    missing_columns = {}

    for table, required_cols in REQUIRED_COLUMNS.items():
        cols = table_columns(conn, table)
        missing = [col for col in required_cols if col not in cols]
        if missing:
            missing_columns[table] = missing

    if missing_columns:
        raise SystemExit(f"Missing required columns: {missing_columns}")

    print("Required columns: OK")

    print("")
    print("Table counts:")
    for table in REQUIRED_TABLES:
        try:
            print(f"- {table}: {table_count(conn, table)}")
        except sqlite3.Error as e:
            print(f"- {table}: count failed: {e}")

    fk_errors = conn.execute("PRAGMA foreign_key_check;").fetchall()
    if fk_errors:
        raise SystemExit(f"Foreign key check failed: {fk_errors}")

    print("")
    print("Foreign key check: OK")

    conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build SQLite database for boatrace prediction system."
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset database before building schema.",
    )
    parser.add_argument(
        "--with-sample-data",
        action="store_true",
        help="Import sample race and odds CSV after schema build.",
    )

    args = parser.parse_args()

    print("STEP 102 database build")

    if args.reset:
        run([PYTHON, "scripts/init_db.py", "--reset"])
    else:
        run([PYTHON, "scripts/init_db.py"])


    validate_schema()

    if args.with_sample_data:
        run([PYTHON, "scripts/import_race_csv.py"])
        run([PYTHON, "scripts/import_odds_csv.py"])
        validate_schema()

    print("")
    print("Database build validation: OK")
    print("STEP 102 CHECK: OK")


if __name__ == "__main__":
    main()
