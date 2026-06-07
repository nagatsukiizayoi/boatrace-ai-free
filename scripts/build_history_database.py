#!/usr/bin/env python3
import csv
import json
import sqlite3
from pathlib import Path

RESULTS_DIR = Path("data/import/history/results")
DB_PATH = Path("db/boatrace.sqlite3")
SUMMARY_PATH = Path("data/import/history/history_database_summary.json")

RESULT_COLUMNS = [
    "race_id",
    "race_date",
    "venue_code",
    "venue_name",
    "race_no",
    "boat_no",
    "racer_id",
    "racer_name",
    "finish_position",
    "start_timing",
    "race_time",
    "winning_decision",
    "weather",
    "wind_direction",
    "wind_speed",
    "wave_height",
    "trifecta_payout",
    "trio_payout",
    "exacta_payout",
    "quinella_payout",
    "source_result_key",
    "source_run_id",
    "source_created_at",
    "source_sheet",
    "note",
]


def read_result_files():
    files = sorted(RESULTS_DIR.glob("results_*.csv"))
    if not files:
        print("ERROR: no results_*.csv files found")
        raise SystemExit(1)
    return files


def create_history_results_table(conn):
    conn.execute("DROP TABLE IF EXISTS history_results")
    conn.execute("DROP TABLE IF EXISTS history_races")

    columns_sql = ", ".join([f"{name} TEXT" for name in RESULT_COLUMNS])
    sql = f"""
    CREATE TABLE history_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        {columns_sql}
    )
    """
    conn.execute(sql)


def insert_history_results(conn, files):
    placeholders = ", ".join(["?"] * len(RESULT_COLUMNS))
    column_names = ", ".join(RESULT_COLUMNS)
    insert_sql = f"""
    INSERT INTO history_results ({column_names})
    VALUES ({placeholders})
    """

    total_rows = 0
    file_stats = []

    for path in files:
        print(f"Importing {path}")
        rows = []

        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                values = []
                for column in RESULT_COLUMNS:
                    values.append((row.get(column) or "").strip())

                if not values[0]:
                    continue

                rows.append(tuple(values))

        conn.executemany(insert_sql, rows)
        total_rows += len(rows)
        file_stats.append({"file": str(path), "rows": len(rows)})
        print(f"  rows: {len(rows)}")

    return file_stats, total_rows


def create_history_races_table(conn):
    conn.execute(
        """
        CREATE TABLE history_races AS
        SELECT
            race_id,
            MIN(race_date) AS race_date,
            MIN(venue_code) AS venue_code,
            MIN(venue_name) AS venue_name,
            MIN(race_no) AS race_no,
            COUNT(*) AS entry_count,
            MAX(trifecta_payout) AS trifecta_payout,
            MAX(trio_payout) AS trio_payout,
            MAX(exacta_payout) AS exacta_payout,
            MAX(quinella_payout) AS quinella_payout
        FROM history_results
        GROUP BY race_id
        """
    )

    conn.execute("CREATE INDEX idx_history_results_race_id ON history_results(race_id)")
    conn.execute("CREATE INDEX idx_history_results_race_date ON history_results(race_date)")
    conn.execute("CREATE INDEX idx_history_results_venue_code ON history_results(venue_code)")
    conn.execute("CREATE INDEX idx_history_results_racer_id ON history_results(racer_id)")
    conn.execute("CREATE INDEX idx_history_races_race_id ON history_races(race_id)")


def fetch_one(conn, sql):
    return conn.execute(sql).fetchone()[0]


def create_summary(conn, file_stats, total_rows):
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

    rows_by_year = []
    for year, count in conn.execute(
        """
        SELECT substr(race_date, 1, 4) AS year, COUNT(*)
        FROM history_results
        GROUP BY substr(race_date, 1, 4)
        ORDER BY year
        """
    ):
        rows_by_year.append({"year": year, "rows": count})

    races_by_year = []
    for year, count in conn.execute(
        """
        SELECT substr(race_date, 1, 4) AS year, COUNT(*)
        FROM history_races
        GROUP BY substr(race_date, 1, 4)
        ORDER BY year
        """
    ):
        races_by_year.append({"year": year, "races": count})

    return {
        "version": "1.0",
        "database_path": str(DB_PATH),
        "source_results_dir": str(RESULTS_DIR),
        "total_rows": total_rows,
        "total_races": total_races,
        "min_race_date": min_date,
        "max_race_date": max_date,
        "venue_count": venue_count,
        "racer_count": racer_count,
        "rows_by_year": rows_by_year,
        "races_by_year": races_by_year,
        "files": file_stats,
        "tables": ["history_results", "history_races"],
    }


def main():
    files = read_result_files()

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)

    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)

    try:
        create_history_results_table(conn)
        file_stats, total_rows = insert_history_results(conn, files)
        create_history_races_table(conn)
        conn.commit()
        summary = create_summary(conn, file_stats, total_rows)
    finally:
        conn.close()

    SUMMARY_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if summary["total_rows"] <= 0:
        print("ERROR: total_rows must be positive")
        raise SystemExit(1)

    if summary["total_races"] <= 0:
        print("ERROR: total_races must be positive")
        raise SystemExit(1)

    print(f"saved database: {DB_PATH}")
    print(f"saved summary: {SUMMARY_PATH}")
    print(f"total rows: {summary['total_rows']}")
    print(f"total races: {summary['total_races']}")
    print("History database build: OK")
    print("STEP 108 CHECK: OK")


if __name__ == "__main__":
    main()
