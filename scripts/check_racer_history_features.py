#!/usr/bin/env python3
import csv
import re
from collections import Counter
from pathlib import Path

FEATURE_PATH = Path("data/import/history/racer_history_features.csv")

REQUIRED_COLUMNS = [
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


def to_int(value):
    try:
        return int(str(value).strip())
    except Exception:
        return None


def to_float(value):
    try:
        return float(str(value).strip())
    except Exception:
        return None


def is_date(value):
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", str(value or "")))


def main():
    errors = []
    warnings = []

    if not FEATURE_PATH.exists():
        print("Racer history features validation: FAILED")
        print(f"ERROR: missing feature CSV: {FEATURE_PATH}")
        raise SystemExit(1)

    with FEATURE_PATH.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []
        rows = list(reader)

    missing = [col for col in REQUIRED_COLUMNS if col not in columns]
    if missing:
        errors.append(f"missing columns: {missing}")

    if not rows:
        errors.append("feature CSV has no data rows")

    racer_ids = []
    invalid_race_count = 0
    invalid_rates = 0
    invalid_rate_order = 0
    invalid_dates = 0
    blank_names = 0

    for row in rows:
        racer_id = (row.get("racer_id") or "").strip()
        racer_name = (row.get("racer_name") or "").strip()

        if not racer_id:
            errors.append("blank racer_id found")
            continue

        racer_ids.append(racer_id)

        if not racer_name:
            blank_names += 1

        race_count = to_int(row.get("race_count"))
        if race_count is None or race_count <= 0:
            invalid_race_count += 1

        win_rate = to_float(row.get("win_rate"))
        top2_rate = to_float(row.get("top2_rate"))
        top3_rate = to_float(row.get("top3_rate"))

        if (
            win_rate is None
            or top2_rate is None
            or top3_rate is None
            or not (0.0 <= win_rate <= 1.0)
            or not (0.0 <= top2_rate <= 1.0)
            or not (0.0 <= top3_rate <= 1.0)
        ):
            invalid_rates += 1
        else:
            if top2_rate + 1e-9 < win_rate or top3_rate + 1e-9 < top2_rate:
                invalid_rate_order += 1

        last_race_date = row.get("last_race_date")
        if last_race_date and not is_date(last_race_date):
            invalid_dates += 1

    duplicated = [item for item, count in Counter(racer_ids).items() if count > 1]

    if invalid_race_count:
        errors.append(f"invalid race_count rows: {invalid_race_count}")
    if invalid_rates:
        errors.append(f"invalid rate rows: {invalid_rates}")
    if invalid_rate_order:
        errors.append(f"invalid rate order rows: {invalid_rate_order}")
    if invalid_dates:
        errors.append(f"invalid last_race_date rows: {invalid_dates}")
    if duplicated:
        errors.append(f"duplicated racer_id count: {len(duplicated)}")
    if blank_names:
        warnings.append(f"rows with blank racer_name: {blank_names}")

    if len(rows) < 100:
        warnings.append(f"racer feature row count is small: {len(rows)}")

    if warnings:
        print("Racer history features validation warnings:")
        for warning in warnings:
            print("WARNING: " + warning)

    if errors:
        print("Racer history features validation: FAILED")
        for error in errors:
            print("ERROR: " + error)
        raise SystemExit(1)

    print(f"racer feature rows: {len(rows)}")
    print("Racer history features validation: OK")
    print("STEP 117 CHECK: OK")


if __name__ == "__main__":
    main()
