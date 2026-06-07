#!/usr/bin/env python3
import csv
import json
from pathlib import Path

FEATURE_PATH = Path("data/import/history/racer_history_features.csv")
OUTPUT_PATH = Path("docs/racer_history_features_summary.json")


def to_int(value):
    try:
        return int(str(value).strip())
    except Exception:
        return 0


def to_float(value):
    try:
        text = str(value).strip()
        if text == "":
            return None
        return float(text)
    except Exception:
        return None


def compact_racer(row):
    return {
        "racer_id": row.get("racer_id", ""),
        "racer_name": row.get("racer_name", ""),
        "race_count": to_int(row.get("race_count")),
        "win_rate": to_float(row.get("win_rate")),
        "top2_rate": to_float(row.get("top2_rate")),
        "top3_rate": to_float(row.get("top3_rate")),
        "avg_start_timing": to_float(row.get("avg_start_timing")),
        "last_race_date": row.get("last_race_date", ""),
    }


def main():
    if not FEATURE_PATH.exists():
        print(f"ERROR: missing feature CSV: {FEATURE_PATH}")
        raise SystemExit(1)

    with FEATURE_PATH.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        print("ERROR: feature CSV has no rows")
        raise SystemExit(1)

    racers = [compact_racer(row) for row in rows]

    racer_count = len(racers)
    total_race_count = sum(item["race_count"] for item in racers)

    win_rates = [item["win_rate"] for item in racers if item["win_rate"] is not None]
    top3_rates = [item["top3_rate"] for item in racers if item["top3_rate"] is not None]
    start_timings = [
        item["avg_start_timing"]
        for item in racers
        if item["avg_start_timing"] is not None
    ]

    latest_dates = sorted(
        [item["last_race_date"] for item in racers if item["last_race_date"]]
    )

    def avg(values):
        return sum(values) / len(values) if values else None

    by_race_count = sorted(
        racers,
        key=lambda item: (item["race_count"], item["top3_rate"] or 0.0),
        reverse=True,
    )[:20]

    by_win_rate = sorted(
        [item for item in racers if item["race_count"] >= 10],
        key=lambda item: (item["win_rate"] or 0.0, item["race_count"]),
        reverse=True,
    )[:20]

    by_top3_rate = sorted(
        [item for item in racers if item["race_count"] >= 10],
        key=lambda item: (item["top3_rate"] or 0.0, item["race_count"]),
        reverse=True,
    )[:20]

    by_start_timing = sorted(
        [item for item in racers if item["avg_start_timing"] is not None and item["race_count"] >= 10],
        key=lambda item: (item["avg_start_timing"], -item["race_count"]),
    )[:20]

    summary = {
        "version": "1.0",
        "source": str(FEATURE_PATH),
        "racer_count": racer_count,
        "total_race_count": total_race_count,
        "average_win_rate": avg(win_rates),
        "average_top3_rate": avg(top3_rates),
        "average_start_timing": avg(start_timings),
        "min_last_race_date": latest_dates[0] if latest_dates else None,
        "max_last_race_date": latest_dates[-1] if latest_dates else None,
        "top_racers_by_race_count": by_race_count,
        "top_racers_by_win_rate": by_win_rate,
        "top_racers_by_top3_rate": by_top3_rate,
        "top_racers_by_start_timing": by_start_timing,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"saved summary: {OUTPUT_PATH}")
    print(f"racer count: {racer_count}")
    print(f"total race count: {total_race_count}")
    print("Racer history feature summary export: OK")
    print("STEP 119 CHECK: OK")


if __name__ == "__main__":
    main()
