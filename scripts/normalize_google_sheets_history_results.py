#!/usr/bin/env python3
import csv
import json
import re
import urllib.request
from collections import defaultdict
from pathlib import Path

SOURCE_CONFIG_PATH = Path("data/history_sources.json")
MAPPING_PATH = Path("data/google_sheets_column_mapping.json")
OUTPUT_DIR = Path("data/import/history/results")

OUTPUT_COLUMNS = [
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


def load_json(path):
    if not path.exists():
        print(f"ERROR: missing file: {path}")
        raise SystemExit(1)
    return json.loads(path.read_text(encoding="utf-8"))


def build_csv_export_url(spreadsheet_id, gid):
    return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"


def download_text(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 history-results-normalizer"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        raw = response.read()
    return raw.decode("utf-8", errors="replace")


def looks_like_html(text):
    head = text[:500].lower()
    return "<html" in head or "<!doctype html" in head or "accounts.google" in head


def clean(value):
    if value is None:
        return ""
    return str(value).strip()


def normalize_date(value):
    value = clean(value)
    if not value:
        return ""
    value = value.replace("/", "-").replace(".", "-")
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", value)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = re.match(r"^(\d{4})(\d{2})(\d{2})$", value)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return value


def year_from_date(value):
    value = normalize_date(value)
    m = re.match(r"^(\d{4})-", value)
    if not m:
        return "unknown"
    return m.group(1)


def normalize_int_like(value, width=None):
    value = clean(value)
    if not value:
        return ""
    m = re.search(r"\d+", value)
    if not m:
        return value
    number = int(m.group(0))
    if width:
        return f"{number:0{width}d}"
    return str(number)


def build_race_id(race_date, venue_code, race_no):
    date_compact = normalize_date(race_date).replace("-", "")
    venue = normalize_int_like(venue_code, width=2)
    race = normalize_int_like(race_no, width=2)
    if not date_compact or not venue or not race:
        return ""
    return f"{date_compact}-{venue}-{race}"


def parse_csv_dicts(text):
    lines = text.splitlines()
    reader = csv.DictReader(lines)
    return list(reader)


def mapping_by_sheet(mapping):
    result = {}
    for sheet in mapping.get("sheets", []):
        name = sheet.get("name")
        if name:
            result[name] = sheet.get("column_mapping", {})
    return result


def normalize_row(row, column_mapping, source_sheet):
    normalized = {col: "" for col in OUTPUT_COLUMNS}

    for source_col, target_col in column_mapping.items():
        if target_col in normalized:
            normalized[target_col] = clean(row.get(source_col, ""))

    normalized["race_date"] = normalize_date(normalized["race_date"])
    normalized["venue_code"] = normalize_int_like(normalized["venue_code"], width=2)
    normalized["race_no"] = normalize_int_like(normalized["race_no"], width=2)
    normalized["boat_no"] = normalize_int_like(normalized["boat_no"])
    normalized["finish_position"] = normalize_int_like(normalized["finish_position"])
    normalized["source_sheet"] = source_sheet
    normalized["race_id"] = build_race_id(
        normalized["race_date"],
        normalized["venue_code"],
        normalized["race_no"],
    )
    return normalized


def main():
    source_config = load_json(SOURCE_CONFIG_PATH)
    mapping = load_json(MAPPING_PATH)
    sheet_mappings = mapping_by_sheet(mapping)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    rows_by_year = defaultdict(list)
    errors = []
    total_rows = 0

    for sheet in source_config.get("google_sheets", []):
        name = sheet.get("name")
        spreadsheet_id = sheet.get("spreadsheet_id")
        gid = str(sheet.get("gid", "0"))
        if not name or not spreadsheet_id:
            errors.append("sheet config missing name or spreadsheet_id")
            continue
        column_mapping = sheet_mappings.get(name)
        if not column_mapping:
            errors.append(f"{name}: missing column mapping")
            continue

        url = build_csv_export_url(spreadsheet_id, gid)
        print(f"Normalizing {name}: gid={gid}")
        try:
            text = download_text(url)
        except Exception as exc:
            errors.append(f"{name}: download failed: {exc}")
            continue

        if looks_like_html(text):
            errors.append(f"{name}: downloaded content looks like HTML")
            continue

        source_rows = parse_csv_dicts(text)
        print(f"  source rows: {len(source_rows)}")
        for row in source_rows:
            normalized = normalize_row(row, column_mapping, name)
            if not normalized["race_date"] and not normalized["race_id"]:
                continue
            year = year_from_date(normalized["race_date"])
            rows_by_year[year].append(normalized)
            total_rows += 1

    if errors:
        print("Google Sheets history results normalization: FAILED")
        for error in errors:
            print("ERROR: " + error)
        raise SystemExit(1)

    if total_rows == 0:
        print("Google Sheets history results normalization: FAILED")
        print("ERROR: no rows were normalized")
        raise SystemExit(1)

    for year, rows in sorted(rows_by_year.items()):
        output_path = OUTPUT_DIR / f"results_{year}.csv"
        with output_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        print(f"  saved: {output_path} rows={len(rows)}")

    print(f"total normalized rows: {total_rows}")
    print("Google Sheets history results normalization: OK")
    print("STEP 106 CHECK: OK")


if __name__ == "__main__":
    main()
