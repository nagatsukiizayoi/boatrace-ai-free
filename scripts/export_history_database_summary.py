#!/usr/bin/env python3
import json
import sqlite3
from pathlib import Path

DB_PATH = Path("db/boatrace.sqlite3")
OUTPUT_PATH = Path("docs/history_database_summary.json")


def table_exists(conn, table_name):
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


def fetch_one(conn, sql, default=0):
    row = conn.execute(sql).fetchone()
    if not row:
        return default
    return row[0]


def fetch_rows(conn, sql):
    return conn.execute(sql).fetchall()


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not DB_PATH.exists():
        summary = {
            "version": "1.0",
            "history_database_available": False,
            "database_path": str(DB_PATH),
            "error": "database file does not exist",
        }
        OUTPUT_PATH.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"saved summary: {OUTPUT_PATH}")
        print("History database summary export: database not available")
        raise SystemExit(1)

    conn = sqlite3.connect(DB_PATH)

    try:
        if not table_exists(conn, "history_results") or not table_exists(conn, "history_races"):
            summary = {
                "version": "1.0",
                "history_database_available": False,
                "database_path": str(DB_PATH),
                "error": "required tables do not exist",
            }
            OUTPUT_PATH.write_text(
                json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(f"saved summary: {OUTPUT_PATH}")
            print("History database summary export: required tables missing")
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

        rows_by_year = [
            {"year": year, "rows": count}
            for year, count in fetch_rows(
                conn,
                """
                SELECT substr(race_date, 1, 4) AS year, COUNT(*)
                FROM history_results
                GROUP BY substr(race_date, 1, 4)
                ORDER BY year
                """,
            )
        ]

        races_by_year = [
            {"year": year, "races": count}
            for year, count in fetch_rows(
                conn,
                """
                SELECT substr(race_date, 1, 4) AS year, COUNT(*)
                FROM history_races
                GROUP BY substr(race_date, 1, 4)
                ORDER BY year
                """,
            )
        ]

        top_venues_by_races = [
            {
                "venue_code": venue_code,
                "venue_name": venue_name,
                "races": count,
            }
            for venue_code, venue_name, count in fetch_rows(
                conn,
                """
                SELECT venue_code, MIN(venue_name), COUNT(*)
                FROM history_races
                GROUP BY venue_code
                ORDER BY COUNT(*) DESC, venue_code
                LIMIT 24
                """,
            )
        ]

        latest_race_dates = [
            {"race_date": race_date, "races": count}
            for race_date, count in fetch_rows(
                conn,
                """
                SELECT race_date, COUNT(*)
                FROM history_races
                GROUP BY race_date
                ORDER BY race_date DESC
                LIMIT 10
                """,
            )
        ]

        summary = {
            "version": "1.0",
            "history_database_available": True,
            "database_path": str(DB_PATH),
            "total_rows": total_rows,
            "total_races": total_races,
            "min_race_date": min_date,
            "max_race_date": max_date,
            "venue_count": venue_count,
            "racer_count": racer_count,
            "rows_by_year": rows_by_year,
            "races_by_year": races_by_year,
            "top_venues_by_races": top_venues_by_races,
            "latest_race_dates": latest_race_dates,
        }

    finally:
        conn.close()

    OUTPUT_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"saved summary: {OUTPUT_PATH}")
    print(f"total rows: {summary['total_rows']}")
    print(f"total races: {summary['total_races']}")
    print("History database summary export: OK")
    print("STEP 110 CHECK: OK")


if __name__ == "__main__":
    main()
