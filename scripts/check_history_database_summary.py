#!/usr/bin/env python3
import json
import re
from pathlib import Path

SUMMARY_PATH = Path("docs/history_database_summary.json")

REQUIRED_TOP_LEVEL_KEYS = [
    "version",
    "history_database_available",
    "database_path",
    "total_rows",
    "total_races",
    "min_race_date",
    "max_race_date",
    "venue_count",
    "racer_count",
    "rows_by_year",
    "races_by_year",
    "top_venues_by_races",
    "latest_race_dates",
]


def is_date(value):
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", str(value or "")))


def main():
    errors = []
    warnings = []

    if not SUMMARY_PATH.exists():
        print("History database summary validation: FAILED")
        print(f"ERROR: missing summary file: {SUMMARY_PATH}")
        raise SystemExit(1)

    try:
        data = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        print("History database summary validation: FAILED")
        print(f"ERROR: invalid JSON: {exc}")
        raise SystemExit(1)

    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in data:
            errors.append(f"missing top-level key: {key}")

    if data.get("history_database_available") is not True:
        errors.append("history_database_available must be true")

    for key in ["total_rows", "total_races", "venue_count", "racer_count"]:
        value = data.get(key)
        if not isinstance(value, int) or value <= 0:
            errors.append(f"{key} must be a positive integer")

    if not is_date(data.get("min_race_date")):
        errors.append("min_race_date must be YYYY-MM-DD")
    if not is_date(data.get("max_race_date")):
        errors.append("max_race_date must be YYYY-MM-DD")
    if is_date(data.get("min_race_date")) and is_date(data.get("max_race_date")):
        if data["min_race_date"] > data["max_race_date"]:
            errors.append("min_race_date must be <= max_race_date")

    rows_by_year = data.get("rows_by_year")
    if not isinstance(rows_by_year, list) or not rows_by_year:
        errors.append("rows_by_year must be a non-empty list")
    else:
        for item in rows_by_year:
            if not isinstance(item, dict):
                errors.append("rows_by_year item must be an object")
                continue
            year = str(item.get("year", ""))
            rows = item.get("rows")
            if not re.match(r"^\d{4}$", year):
                errors.append(f"rows_by_year invalid year: {year}")
            if not isinstance(rows, int) or rows <= 0:
                errors.append(f"rows_by_year rows must be positive for year: {year}")

    races_by_year = data.get("races_by_year")
    if not isinstance(races_by_year, list) or not races_by_year:
        errors.append("races_by_year must be a non-empty list")
    else:
        for item in races_by_year:
            if not isinstance(item, dict):
                errors.append("races_by_year item must be an object")
                continue
            year = str(item.get("year", ""))
            races = item.get("races")
            if not re.match(r"^\d{4}$", year):
                errors.append(f"races_by_year invalid year: {year}")
            if not isinstance(races, int) or races <= 0:
                errors.append(f"races_by_year races must be positive for year: {year}")

    top_venues = data.get("top_venues_by_races")
    if not isinstance(top_venues, list) or not top_venues:
        errors.append("top_venues_by_races must be a non-empty list")
    else:
        for item in top_venues[:5]:
            if not isinstance(item, dict):
                errors.append("top_venues_by_races item must be an object")
                continue
            if not item.get("venue_code"):
                errors.append("top_venues_by_races item missing venue_code")
            if "races" not in item or not isinstance(item.get("races"), int):
                errors.append("top_venues_by_races item races must be integer")

    latest = data.get("latest_race_dates")
    if not isinstance(latest, list) or not latest:
        errors.append("latest_race_dates must be a non-empty list")
    else:
        for item in latest[:5]:
            if not isinstance(item, dict):
                errors.append("latest_race_dates item must be an object")
                continue
            if not is_date(item.get("race_date")):
                errors.append("latest_race_dates item race_date must be YYYY-MM-DD")
            if "races" not in item or not isinstance(item.get("races"), int):
                errors.append("latest_race_dates item races must be integer")

    expected_years = {"2023", "2024", "2025", "2026"}
    actual_years = {str(item.get("year")) for item in rows_by_year or [] if isinstance(item, dict)}
    missing_years = sorted(expected_years - actual_years)
    if missing_years:
        warnings.append(f"expected years not found in rows_by_year: {missing_years}")

    if warnings:
        print("History database summary validation warnings:")
        for warning in warnings:
            print("WARNING: " + warning)

    if errors:
        print("History database summary validation: FAILED")
        for error in errors:
            print("ERROR: " + error)
        raise SystemExit(1)

    print("History database summary validation: OK")
    print("STEP 111 CHECK: OK")


if __name__ == "__main__":
    main()
