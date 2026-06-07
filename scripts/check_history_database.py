#!/usr/bin/env python3
import json
import sqlite3
from pathlib import Path

DB_PATH = Path("db/boatrace.sqlite3")
SUMMARY_PATH = Path("data/import/history/history_database_summary.json")

REQUIRED_TABLES = [
    "history_results",
    "history_races",
]


def load_summary():
    if not SUMMARY_PATH.exists():
        print(f"ERROR: missing summary file: {SUMMARY_PATH}")
        raise SystemExit(1)
    return json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))


def table_exists(conn, table_name):
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


def fetch_one(conn, sql):
    return conn.execute(sql).fetchone()[0]


def main():
    errors = []
    warnings = []

    if not DB_PATH.exists():
        errors.append(f"missing database file: {DB_PATH}")

    summary = {}
    if SUMMARY_PATH.exists():
        try:
            summary = load_summary()
        except Exception as exc:
            errors.append(f"invalid summary JSON: {exc}")
    else:
        errors.append(f"missing summary file: {SUMMARY_PATH}")

    if errors:
        print("History database validation: FAILED")
        for error in errors:
            print("ERROR: " + error)
        raise SystemExit(1)

    conn = sqlite3.connect(DB_PATH)

    try:
        for table in REQUIRED_TABLES:
            if not table_exists(conn, table):
                errors.append(f"missing table: {table}")

        if errors:
            print("History database validation: FAILED")
            for error in errors:
                print("ERROR: " + error)
            raise SystemExit(1)

        total_rows = fetch_one(conn, "SELECT COUNT(*) FROM history_results")
        total_races = fetch_one(conn, "SELECT COUNT(*) FROM history_races")

        min_date, max_date = conn.execute(
            "SELECT MIN(race_date), MAX(race_date) FROM history_results"
        ).fetchone()

        venue_count = fetch_one(
            conn,
            "SELECT COUNT(DISTINCT venue_code) FROM history_results",
        )

        racer_count = fetch_one(
            conn,
            "SELECT COUNT(DISTINCT racer_id) FROM history_results WHERE racer_id != ''",
        )

        years = [
            row[0]
            for row in conn.execute(
                """
                SELECT DISTINCT substr(race_date, 1, 4) AS year
                FROM history_results
                WHERE race_date != ''
                ORDER BY year
                """
            )
        ]

        if total_rows <= 0:
            errors.append("history_results row count must be positive")
        if total_races <= 0:
            errors.append("history_races row count must be positive")
        if not min_date or not max_date:
            errors.append("race_date min/max must exist")
        if venue_count <= 0:
            errors.append("venue_count must be positive")
        if racer_count <= 0:
            errors.append("racer_count must be positive")

        for expected_year in ["2023", "2024", "2025", "2026"]:
            if expected_year not in years:
                warnings.append(f"expected year not found in DB: {expected_year}")

        summary_total_rows = summary.get("total_rows")
        summary_total_races = summary.get("total_races")
        summary_min_date = summary.get("min_race_date")
        summary_max_date = summary.get("max_race_date")

        if summary_total_rows != total_rows:
            errors.append(
                f"summary total_rows mismatch: summary={summary_total_rows}, db={total_rows}"
            )

        if summary_total_races != total_races:
            errors.append(
                f"summary total_races mismatch: summary={summary_total_races}, db={total_races}"
            )

        if summary_min_date != min_date:
            errors.append(
                f"summary min_race_date mismatch: summary={summary_min_date}, db={min_date}"
            )

        if summary_max_date != max_date:
            errors.append(
                f"summary max_race_date mismatch: summary={summary_max_date}, db={max_date}"
            )

        print(f"database: {DB_PATH}")
        print(f"total rows: {total_rows}")
        print(f"total races: {total_races}")
        print(f"date range: {min_date} - {max_date}")
        print(f"venue count: {venue_count}")
        print(f"racer count: {racer_count}")
        print(f"years: {years}")

    finally:
        conn.close()

    if warnings:
        print("History database validation warnings:")
        for warning in warnings:
            print("WARNING: " + warning)

    if errors:
        print("History database validation: FAILED")
        for error in errors:
            print("ERROR: " + error)
        raise SystemExit(1)

    print("History database validation: OK")
    print("STEP 109 CHECK: OK")


if __name__ == "__main__":
    main()
