#!/usr/bin/env python3
import sqlite3
import sys
from pathlib import Path


DB_PATH = Path("db/boatrace.sqlite3")


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


MIN_COUNTS_WITH_SAMPLE = {
    "venues": 1,
    "racers": 12,
    "races": 2,
    "race_entries": 12,
    "odds_snapshots": 18,
}


REQUIRED_COLUMNS = {
    "races": [
        "id",
        "race_date",
        "venue_id",
        "race_no",
    ],
    "racers": [
        "id",
    ],
    "race_entries": [
        "id",
        "race_id",
        "racer_id",
    ],
    "odds_snapshots": [
        "id",
        "race_id",
        "bet_type",
        "combination",
        "odds",
    ],
    "prediction_tickets": [
        "id",
        "prediction_id",
        "bet_type",
        "combination",
        "odds",
        "expected_value",
    ],
}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


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


def main() -> None:
    if not DB_PATH.exists():
        fail(f"Database file does not exist: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    print("Database:", DB_PATH)
    print("SQLite version:", sqlite3.sqlite_version)

    missing_tables = [table for table in REQUIRED_TABLES if not table_exists(conn, table)]
    if missing_tables:
        fail(f"Missing required tables: {missing_tables}")

    print("Required tables: OK")

    missing_columns = {}

    for table, required_cols in REQUIRED_COLUMNS.items():
        cols = table_columns(conn, table)
        missing = [col for col in required_cols if col not in cols]
        if missing:
            missing_columns[table] = missing

    if missing_columns:
        fail(f"Missing required columns: {missing_columns}")

    print("Required columns: OK")

    print("Table counts:")
    counts = {}

    for table in REQUIRED_TABLES:
        count = table_count(conn, table)
        counts[table] = count
        print(f"- {table}: {count}")

    count_errors = []

    for table, min_count in MIN_COUNTS_WITH_SAMPLE.items():
        actual = counts.get(table, 0)
        if actual < min_count:
            count_errors.append(f"{table}: expected >= {min_count}, got {actual}")

    if count_errors:
        for e in count_errors:
            print("-", e)
        fail("Sample data count validation failed")

    print("Sample data counts: OK")

    bet_type_rows = conn.execute("""
        SELECT bet_type, COUNT(*)
        FROM odds_snapshots
        GROUP BY bet_type
        ORDER BY bet_type
    """).fetchall()

    allowed_bet_types = {
        "tansho",
        "fukusho",
        "2rentan",
        "2renfuku",
        "3rentan",
        "3renfuku",
        "kakuren",
        "unknown",
    }

    actual_bet_types = {row[0] for row in bet_type_rows}
    invalid_bet_types = actual_bet_types - allowed_bet_types

    print("odds_snapshots bet_type counts:")
    for bet_type, count in bet_type_rows:
        print(f"- {bet_type}: {count}")

    if invalid_bet_types:
        fail(f"Invalid bet_type values in odds_snapshots: {sorted(invalid_bet_types)}")

    print("bet_type validation: OK")

    non_positive_odds = conn.execute("""
        SELECT COUNT(*)
        FROM odds_snapshots
        WHERE odds IS NULL OR odds <= 0
    """).fetchone()[0]

    if non_positive_odds > 0:
        fail(f"odds_snapshots has non-positive odds rows: {non_positive_odds}")

    print("odds positive validation: OK")

    fk_errors = conn.execute("PRAGMA foreign_key_check;").fetchall()
    if fk_errors:
        fail(f"Foreign key check failed: {fk_errors}")

    print("Foreign key check: OK")

    conn.close()

    print("Database build check: OK")
    print("STEP 103 CHECK: OK")


if __name__ == "__main__":
    main()
