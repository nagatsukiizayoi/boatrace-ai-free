#!/usr/bin/env python3
import json
from pathlib import Path

PROFILE_PATH = Path("data/import/google_sheets/google_sheets_history_profile.json")

REQUIRED_SHEETS = {
    "google_sheet_1": "677335535",
    "google_sheet_2": "100303855",
    "google_sheet_3": "1985626131",
    "google_sheet_4": "464226554",
}


def main():
    errors = []
    warnings = []

    if not PROFILE_PATH.exists():
        errors.append("missing profile file: data/import/google_sheets/google_sheets_history_profile.json")
        data = {}
    else:
        try:
            data = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append("invalid profile JSON: " + str(exc))
            data = {}

    profiles = data.get("profiles", []) if isinstance(data, dict) else []
    if not isinstance(profiles, list):
        errors.append("profiles must be a list")
        profiles = []

    if data.get("profile_count") != len(profiles):
        errors.append("profile_count mismatch")

    if len(profiles) < 4:
        errors.append("profile_count must be at least 4")

    by_name = {}
    for profile in profiles:
        if not isinstance(profile, dict):
            errors.append("profile entry must be an object")
            continue

        name = profile.get("name")
        if not name:
            errors.append("profile missing name")
            continue

        by_name[name] = profile

        spreadsheet_id = profile.get("spreadsheet_id")
        gid = str(profile.get("gid", ""))
        row_count = profile.get("row_count")
        data_row_count = profile.get("data_row_count")
        column_count = profile.get("column_count")
        columns = profile.get("columns")
        sample_rows = profile.get("sample_rows")
        empty_columns = profile.get("empty_columns", [])
        duplicate_columns = profile.get("duplicate_columns", [])

        if not spreadsheet_id:
            errors.append(f"{name}: missing spreadsheet_id")
        if not gid:
            errors.append(f"{name}: missing gid")
        if not isinstance(row_count, int) or row_count <= 0:
            errors.append(f"{name}: row_count must be positive")
        if not isinstance(data_row_count, int) or data_row_count < 0:
            errors.append(f"{name}: data_row_count must be zero or positive")
        if not isinstance(column_count, int) or column_count <= 0:
            errors.append(f"{name}: column_count must be positive")
        if not isinstance(columns, list) or not columns:
            errors.append(f"{name}: columns must be a non-empty list")
        if isinstance(columns, list) and column_count != len(columns):
            errors.append(f"{name}: column_count does not match columns length")
        if not isinstance(sample_rows, list):
            errors.append(f"{name}: sample_rows must be a list")
        elif data_row_count > 0 and not sample_rows:
            warnings.append(f"{name}: sample_rows is empty even though data rows exist")

        if empty_columns:
            warnings.append(f"{name}: has empty columns: {empty_columns}")
        if duplicate_columns:
            warnings.append(f"{name}: has duplicate columns: {duplicate_columns}")
        if isinstance(column_count, int) and column_count < 3:
            warnings.append(f"{name}: column_count is very small: {column_count}")

    for required_name, required_gid in REQUIRED_SHEETS.items():
        profile = by_name.get(required_name)
        if not profile:
            errors.append(f"missing required profile: {required_name}")
            continue
        if str(profile.get("gid", "")) != required_gid:
            errors.append(f"{required_name}: gid mismatch, expected {required_gid}")

    if warnings:
        print("Google Sheets history profile validation warnings:")
        for warning in warnings:
            print("WARNING: " + warning)

    if errors:
        print("Google Sheets history profile validation: FAILED")
        for error in errors:
            print("ERROR: " + error)
        raise SystemExit(1)

    print("Google Sheets history profile validation: OK")
    print("STEP 104 CHECK: OK")


if __name__ == "__main__":
    main()
