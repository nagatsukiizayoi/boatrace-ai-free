#!/usr/bin/env python3
import csv
import sqlite3
from pathlib import Path

DB_PATH = Path("db/boatrace.sqlite3")
OUTPUT_PATH = Path("data/import/history/racer_history_features.csv")

OUTPUT_COLUMNS = [
    "racer_id",
    "racer_name",
    "race_count",
    "win_count",
    "top2_count",
    "top3_count",
    "win_rate",
    "top2_rate",
    "top3_rate",
    "avg_start_timing",
    "last_race_date",
]


def to_float(value):
    try:
        if value is None:
            return None
        text = str(value).strip()
        if text == "":
            return None
        return float(text)
    except Exception:
        return None


def main():
    if not DB_PATH.exists():
        print(f"ERROR: missing database: {DB_PATH}")
        raise SystemExit(1)

    conn = sqlite3.connect(DB_PATH)

    try:
        rows = conn.execute(
            """
            SELECT
                racer_id,
                MAX(racer_name) AS racer_name,
                COUNT(*) AS race_count,
                SUM(CASE WHEN finish_position = '1' THEN 1 ELSE 0 END) AS win_count,
                SUM(CASE WHEN finish_position IN ('1', '2') THEN 1 ELSE 0 END) AS top2_count,
                SUM(CASE WHEN finish_position IN ('1', '2', '3') THEN 1 ELSE 0 END) AS top3_count,
                MAX(race_date) AS last_race_date
            FROM history_results
            WHERE racer_id != ''
            GROUP BY racer_id
            ORDER BY racer_id
            """
        ).fetchall()

        start_rows = conn.execute(
            """
            SELECT racer_id, start_timing
            FROM history_results
            WHERE racer_id != '' AND start_timing != ''
            """
        ).fetchall()

    finally:
        conn.close()

    st_values = {}
    for racer_id, start_timing in start_rows:
        value = to_float(start_timing)
        if value is None:
            continue
        st_values.setdefault(racer_id, []).append(value)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    output_rows = []

    for (
        racer_id,
        racer_name,
        race_count,
        win_count,
        top2_count,
        top3_count,
        last_race_date,
    ) in rows:
        race_count = int(race_count or 0)
        win_count = int(win_count or 0)
        top2_count = int(top2_count or 0)
        top3_count = int(top3_count or 0)

        if race_count > 0:
            win_rate = win_count / race_count
            top2_rate = top2_count / race_count
            top3_rate = top3_count / race_count
        else:
            win_rate = 0.0
            top2_rate = 0.0
            top3_rate = 0.0

        starts = st_values.get(racer_id, [])
        if starts:
            avg_start_timing = sum(starts) / len(starts)
        else:
            avg_start_timing = ""

        output_rows.append({
            "racer_id": racer_id,
            "racer_name": racer_name or "",
            "race_count": race_count,
            "win_count": win_count,
            "top2_count": top2_count,
            "top3_count": top3_count,
            "win_rate": f"{win_rate:.6f}",
            "top2_rate": f"{top2_rate:.6f}",
            "top3_rate": f"{top3_rate:.6f}",
            "avg_start_timing": f"{avg_start_timing:.4f}" if avg_start_timing != "" else "",
            "last_race_date": last_race_date or "",
        })

    with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(output_rows)

    if not output_rows:
        print("ERROR: no racer history features generated")
        raise SystemExit(1)

    print(f"saved features: {OUTPUT_PATH}")
    print(f"racer count: {len(output_rows)}")
    print("Racer history feature build: OK")
    print("STEP 116 CHECK: OK")


if __name__ == "__main__":
    main()
