#!/usr/bin/env python3
import csv
import json
import urllib.request
from collections import Counter
from pathlib import Path

CONFIG_PATH = Path("data/history_sources.json")
PROFILE_OUTPUT_PATH = Path("data/import/google_sheets/google_sheets_history_profile.json")


def read_config():
    if not CONFIG_PATH.exists():
        print("ERROR: missing data/history_sources.json")
        raise SystemExit(1)
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def build_csv_export_url(spreadsheet_id, gid):
    return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"


def download_text(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 history-source-profiler"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        raw = response.read()
    return raw.decode("utf-8", errors="replace")


def looks_like_html(text):
    head = text[:500].lower()
    return "<html" in head or "<!doctype html" in head or "accounts.google" in head


def normalize_header(header):
    normalized = []
    for idx, value in enumerate(header):
        value = value.strip()
        if not value:
            value = f"__empty_column_{idx + 1}"
        normalized.append(value)
    return normalized


def profile_csv_text(text):
    rows = list(csv.reader(text.splitlines()))
    non_empty_rows = [row for row in rows if any(cell.strip() for cell in row)]
    if not non_empty_rows:
        return {
            "row_count": 0,
            "data_row_count": 0,
            "column_count": 0,
            "columns": [],
            "empty_columns": [],
            "duplicate_columns": [],
            "sample_rows": [],
        }

    raw_header = non_empty_rows[0]
    columns = normalize_header(raw_header)
    counter = Counter(columns)
    duplicate_columns = sorted([name for name, count in counter.items() if count > 1])
    empty_columns = [name for name in columns if name.startswith("__empty_column_")]

    sample_rows = []
    for row in non_empty_rows[1:6]:
        padded = row + [""] * max(0, len(columns) - len(row))
        sample_rows.append({columns[i]: padded[i] if i < len(padded) else "" for i in range(len(columns))})

    return {
        "row_count": len(non_empty_rows),
        "data_row_count": max(0, len(non_empty_rows) - 1),
        "column_count": len(columns),
        "columns": columns,
        "empty_columns": empty_columns,
        "duplicate_columns": duplicate_columns,
        "sample_rows": sample_rows,
    }


def main():
    config = read_config()
    sheets = config.get("google_sheets", [])
    if not isinstance(sheets, list) or not sheets:
        print("ERROR: google_sheets is empty or invalid")
        raise SystemExit(1)

    profiles = []
    errors = []

    for item in sheets:
        name = item.get("name", "unknown_sheet")
        spreadsheet_id = item.get("spreadsheet_id")
        gid = str(item.get("gid", "0"))
        if not spreadsheet_id:
            errors.append(f"{name}: missing spreadsheet_id")
            continue

        url = build_csv_export_url(spreadsheet_id, gid)
        print(f"Profiling {name}: gid={gid}")
        try:
            text = download_text(url)
        except Exception as exc:
            errors.append(f"{name}: download failed: {exc}")
            continue

        if looks_like_html(text):
            errors.append(f"{name}: downloaded content looks like HTML")
            continue

        profile = profile_csv_text(text)
        if profile["row_count"] == 0:
            errors.append(f"{name}: CSV appears to be empty")
            continue

        profiles.append({
            "name": name,
            "spreadsheet_id": spreadsheet_id,
            "gid": gid,
            "csv_export_url": url,
            **profile,
        })

        print(f"  rows: {profile['row_count']}")
        print(f"  data rows: {profile['data_row_count']}")
        print(f"  columns: {profile['column_count']}")
        if profile["empty_columns"]:
            print(f"  empty columns: {profile['empty_columns']}")
        if profile["duplicate_columns"]:
            print(f"  duplicate columns: {profile['duplicate_columns']}")

    if errors:
        print("Google Sheets history source profiling: FAILED")
        for error in errors:
            print("ERROR: " + error)
        raise SystemExit(1)

    result = {
        "version": "1.0",
        "source_config": str(CONFIG_PATH),
        "profile_count": len(profiles),
        "profiles": profiles,
    }

    PROFILE_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_OUTPUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"saved profile: {PROFILE_OUTPUT_PATH}")
    print("Google Sheets history source profiling: OK")
    print("STEP 103 CHECK: OK")


if __name__ == "__main__":
    main()
