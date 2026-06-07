#!/usr/bin/env python3
import json
from pathlib import Path

SUMMARY_PATH = Path("docs/racer_history_features_summary.json")

REQUIRED_TOP_LEVEL_KEYS = [
    "version",
    "source",
    "racer_count",
    "total_race_count",
    "average_win_rate",
    "average_top3_rate",
    "average_start_timing",
    "min_last_race_date",
    "max_last_race_date",
    "top_racers_by_race_count",
    "top_racers_by_win_rate",
    "top_racers_by_top3_rate",
    "top_racers_by_start_timing",
]

RANKING_KEYS = [
    "top_racers_by_race_count",
    "top_racers_by_win_rate",
    "top_racers_by_top3_rate",
    "top_racers_by_start_timing",
]


def is_number_or_none(value):
    return value is None or isinstance(value, (int, float))


def rate_is_valid(value):
    return value is None or (
        isinstance(value, (int, float)) and 0.0 <= value <= 1.0
    )


def main():
    errors = []
    warnings = []

    if not SUMMARY_PATH.exists():
        print("Racer history feature summary validation: FAILED")
        print(f"ERROR: missing summary file: {SUMMARY_PATH}")
        raise SystemExit(1)

    try:
        data = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        print("Racer history feature summary validation: FAILED")
        print(f"ERROR: invalid JSON: {exc}")
        raise SystemExit(1)

    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in data:
            errors.append(f"missing top-level key: {key}")

    racer_count = data.get("racer_count")
    total_race_count = data.get("total_race_count")

    if not isinstance(racer_count, int) or racer_count <= 0:
        errors.append("racer_count must be a positive integer")

    if not isinstance(total_race_count, int) or total_race_count <= 0:
        errors.append("total_race_count must be a positive integer")

    if (
        isinstance(racer_count, int)
        and isinstance(total_race_count, int)
        and total_race_count < racer_count
    ):
        warnings.append("total_race_count is smaller than racer_count")

    for key in ["average_win_rate", "average_top3_rate"]:
        if not rate_is_valid(data.get(key)):
            errors.append(f"{key} must be between 0 and 1 or null")

    if not is_number_or_none(data.get("average_start_timing")):
        errors.append("average_start_timing must be number or null")

    for ranking_key in RANKING_KEYS:
        ranking = data.get(ranking_key)
        if not isinstance(ranking, list) or not ranking:
            errors.append(f"{ranking_key} must be a non-empty list")
            continue

        for idx, item in enumerate(ranking[:20], start=1):
            if not isinstance(item, dict):
                errors.append(f"{ranking_key}[{idx}] must be an object")
                continue

            if not item.get("racer_id"):
                errors.append(f"{ranking_key}[{idx}] missing racer_id")

            if "racer_name" not in item:
                errors.append(f"{ranking_key}[{idx}] missing racer_name")

            race_count = item.get("race_count")
            if not isinstance(race_count, int) or race_count <= 0:
                errors.append(f"{ranking_key}[{idx}] invalid race_count")

            for rate_key in ["win_rate", "top2_rate", "top3_rate"]:
                if not rate_is_valid(item.get(rate_key)):
                    errors.append(f"{ranking_key}[{idx}] invalid {rate_key}")

            avg_start = item.get("avg_start_timing")
            if not is_number_or_none(avg_start):
                errors.append(f"{ranking_key}[{idx}] invalid avg_start_timing")

    if warnings:
        print("Racer history feature summary validation warnings:")
        for warning in warnings:
            print("WARNING: " + warning)

    if errors:
        print("Racer history feature summary validation: FAILED")
        for error in errors:
            print("ERROR: " + error)
        raise SystemExit(1)

    print("Racer history feature summary validation: OK")
    print("STEP 120 CHECK: OK")


if __name__ == "__main__":
    main()
