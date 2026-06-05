#!/usr/bin/env python3
import json
from pathlib import Path

MAPPING_PATH = Path("data/google_sheets_column_mapping.json")
PROFILE_PATH = Path("data/import/google_sheets/google_sheets_history_profile.json")

REQUIRED_SHEETS = {
    "google_sheet_1": "677335535",
    "google_sheet_2": "100303855",
    "google_sheet_3": "1985626131",
    "google_sheet_4": "464226554",
}

REQUIRED_STANDARD_COLUMNS = [
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
]


def load_json(path):
    if not path.exists():
        raise FileNotFoundError(str(path))
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    errors = []
    warnings = []

    try:
        mapping = load_json(MAPPING_PATH)
    except Exception as exc:
        print("Google Sheets column mapping validation: FAILED")
        print("ERROR: cannot load mapping: " + str(exc))
        raise SystemExit(1)

    try:
        profile = load_json(PROFILE_PATH)
    except Exception as exc:
        print("Google Sheets column mapping validation: FAILED")
        print("ERROR: cannot load profile: " + str(exc))
        raise SystemExit(1)

    for key in ["version", "source_profile", "standard_dataset", "race_id_rule", "output_targets", "sheets"]:
        if key not in mapping:
            errors.append("missing mapping top-level key: " + key)

    if mapping.get("standard_dataset") != "race_results_long":
        errors.append("standard_dataset must be race_results_long")

    race_id_rule = mapping.get("race_id_rule", {})
    if race_id_rule.get("format") != "YYYYMMDD-venue_code-race_no":
        errors.append("race_id_rule.format mismatch")
    for col in ["date", "jcd", "race"]:
        if col not in race_id_rule.get("source_columns", []):
            errors.append("race_id_rule missing source column: " + col)

    profiles = profile.get("profiles", [])
    profile_by_name = {}
    seen_profile_names = set()
    for item in profiles:
        name = item.get("name")
        if not name:
            continue
        if name in seen_profile_names:
            warnings.append("duplicate profile name found: " + name)
        seen_profile_names.add(name)
        profile_by_name[name] = item

    sheets = mapping.get("sheets", [])
    if not isinstance(sheets, list) or len(sheets) < 4:
        errors.append("mapping.sheets must contain at least 4 entries")
        sheets = []

    sheet_names = set()
    for sheet in sheets:
        name = sheet.get("name")
        gid = str(sheet.get("gid", ""))
        column_mapping = sheet.get("column_mapping", {})
        required_source_columns = sheet.get("required_source_columns", [])

        if not name:
            errors.append("sheet mapping missing name")
            continue
        sheet_names.add(name)

        expected_gid = REQUIRED_SHEETS.get(name)
        if expected_gid and gid != expected_gid:
            errors.append(f"{name}: gid mismatch, expected {expected_gid}")

        profile_item = profile_by_name.get(name)
        if not profile_item:
            errors.append(f"{name}: missing source profile")
            continue

        profile_gid = str(profile_item.get("gid", ""))
        if expected_gid and profile_gid != expected_gid:
            errors.append(f"{name}: profile gid mismatch, expected {expected_gid}")

        source_columns = set(profile_item.get("columns", []))
        for source_col in required_source_columns:
            if source_col not in source_columns:
                errors.append(f"{name}: required source column not found in profile: {source_col}")

        if not isinstance(column_mapping, dict) or not column_mapping:
            errors.append(f"{name}: column_mapping must be non-empty")
            continue

        for source_col, standard_col in column_mapping.items():
            if source_col not in source_columns:
                errors.append(f"{name}: mapped source column not found in profile: {source_col}")
            if not standard_col:
                errors.append(f"{name}: empty standard column for source: {source_col}")

        standard_columns = set(column_mapping.values())
        for standard_col in REQUIRED_STANDARD_COLUMNS:
            if standard_col not in standard_columns:
                errors.append(f"{name}: missing required standard column mapping: {standard_col}")

    for required_name in REQUIRED_SHEETS:
        if required_name not in sheet_names:
            errors.append("missing required sheet mapping: " + required_name)

    if warnings:
        print("Google Sheets column mapping validation warnings:")
        for warning in warnings:
            print("WARNING: " + warning)

    if errors:
        print("Google Sheets column mapping validation: FAILED")
        for error in errors:
            print("ERROR: " + error)
        raise SystemExit(1)

    print("Google Sheets column mapping validation: OK")
    print("STEP 105 CHECK: OK")


if __name__ == "__main__":
    main()
