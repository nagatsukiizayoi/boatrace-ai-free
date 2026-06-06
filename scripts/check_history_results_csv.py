#!/usr/bin/env python3
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

RESULTS_DIR = Path("data/import/history/results")

REQUIRED_COLUMNS = [
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


def is_date(value):
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", value or ""))


def is_two_digit(value):
    return bool(re.match(r"^\d{2}$", value or ""))


def int_or_none(value):
    try:
        if value is None or str(value).strip() == "":
            return None
        return int(float(str(value).strip()))
    except Exception:
        return None


def year_from_filename(path):
    m = re.search(r"results_(\d{4}|unknown)\.csv$", path.name)
    return m.group(1) if m else None


def main():
    errors = []
    warnings = []

    files = sorted(RESULTS_DIR.glob("results_*.csv"))
    if not files:
        errors.append("no results_*.csv files found")

    total_rows = 0
    total_races = set()

    for path in files:
        file_year = year_from_filename(path)
        if not file_year:
            errors.append(f"invalid results CSV filename: {path}")
            continue

        print(f"Checking {path}")
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            columns = reader.fieldnames or []
            rows = list(reader)

        if not rows:
            errors.append(f"{path}: no data rows")
            continue

        missing = [col for col in REQUIRED_COLUMNS if col not in columns]
        if missing:
            errors.append(f"{path}: missing columns: {missing}")

        row_count = len(rows)
        total_rows += row_count
        race_counter = Counter()
        race_boats = defaultdict(set)
        race_finish_positions = defaultdict(set)

        invalid_race_id = 0
        invalid_date = 0
        invalid_venue = 0
        invalid_race_no = 0
        invalid_boat_no = 0
        invalid_finish = 0
        year_mismatch = 0
        blank_racer = 0

        for idx, row in enumerate(rows, start=2):
            race_id = (row.get("race_id") or "").strip()
            race_date = (row.get("race_date") or "").strip()
            venue_code = (row.get("venue_code") or "").strip()
            race_no = (row.get("race_no") or "").strip()
            boat_no = (row.get("boat_no") or "").strip()
            finish_position = (row.get("finish_position") or "").strip()
            racer_id = (row.get("racer_id") or "").strip()
            racer_name = (row.get("racer_name") or "").strip()

            if not re.match(r"^\d{8}-\d{2}-\d{2}$", race_id):
                invalid_race_id += 1
            if not is_date(race_date):
                invalid_date += 1
            else:
                if file_year != "unknown" and not race_date.startswith(file_year + "-"):
                    year_mismatch += 1
            if not is_two_digit(venue_code):
                invalid_venue += 1
            if not is_two_digit(race_no):
                invalid_race_no += 1

            boat_int = int_or_none(boat_no)
            if boat_int is None or not (1 <= boat_int <= 6):
                invalid_boat_no += 1

            finish_int = int_or_none(finish_position)
            if finish_int is None or not (1 <= finish_int <= 6):
                invalid_finish += 1

            if not racer_id and not racer_name:
                blank_racer += 1

            if race_id:
                race_counter[race_id] += 1
                total_races.add(race_id)
                if boat_int is not None:
                    race_boats[race_id].add(boat_int)
                if finish_int is not None:
                    race_finish_positions[race_id].add(finish_int)

        if invalid_race_id:
            errors.append(f"{path}: invalid race_id rows: {invalid_race_id}")
        if invalid_date:
            errors.append(f"{path}: invalid race_date rows: {invalid_date}")
        if invalid_venue:
            errors.append(f"{path}: invalid venue_code rows: {invalid_venue}")
        if invalid_race_no:
            errors.append(f"{path}: invalid race_no rows: {invalid_race_no}")
        if invalid_boat_no:
            errors.append(f"{path}: invalid boat_no rows: {invalid_boat_no}")
        if invalid_finish:
            warnings.append(f"{path}: non-numeric or non-standard finish_position rows: {invalid_finish}")
        if year_mismatch:
            errors.append(f"{path}: race_date year mismatch rows: {year_mismatch}")
        if blank_racer:
            warnings.append(f"{path}: rows with blank racer_id and racer_name: {blank_racer}")

        oversized_races = [race_id for race_id, count in race_counter.items() if count > 6]
        if oversized_races:
            warnings.append(f"{path}: races with more than 6 rows: {len(oversized_races)}")

        undersized_races = [race_id for race_id, count in race_counter.items() if count < 1]
        if undersized_races:
            warnings.append(f"{path}: races with less than 1 row: {len(undersized_races)}")

        print(f"  rows: {row_count}")
        print(f"  races: {len(race_counter)}")

    if warnings:
        print("History results CSV validation warnings:")
        for warning in warnings:
            print("WARNING: " + warning)

    if errors:
        print("History results CSV validation: FAILED")
        for error in errors:
            print("ERROR: " + error)
        raise SystemExit(1)

    print(f"total rows: {total_rows}")
    print(f"total races: {len(total_races)}")
    print("History results CSV validation: OK")
    print("STEP 107 CHECK: OK")


if __name__ == "__main__":
    main()
