#!/usr/bin/env python3
import csv
import json
import urllib.request
from pathlib import Path

CONFIG_PATH = Path("data/history_sources.json")
RAW_OUTPUT_DIR = Path("data/raw/google_sheets")


def read_config():
    if not CONFIG_PATH.exists():
        print("ERROR: missing data/history_sources.json")
        raise SystemExit(1)
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def build_csv_export_url(spreadsheet_id, gid="0"):
    return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"


def download_text(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 history-source-inspector"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        raw = response.read()
    return raw.decode("utf-8", errors="replace")


def looks_like_html(text):
    head = text[:500].lower()
    return "<html" in head or "<!doctype html" in head or "accounts.google" in head


def inspect_csv_text(text):
    rows = list(csv.reader(text.splitlines()))
    non_empty = [row for row in rows if any(cell.strip() for cell in row)]
    if not non_empty:
        return [], 0
    header = [cell.strip() for cell in non_empty[0]]
    return header, len(non_empty)


def main():
    config = read_config()
    sheets = config.get("google_sheets", [])
    if not isinstance(sheets, list) or not sheets:
        print("ERROR: google_sheets is empty or invalid")
        raise SystemExit(1)

    RAW_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    errors = []

    for item in sheets:
        name = item.get("name", "unknown_sheet")
        spreadsheet_id = item.get("spreadsheet_id")
        if not spreadsheet_id:
            errors.append(f"{name}: missing spreadsheet_id")
            continue

        gid = str(item.get("gid", "0"))
        url = build_csv_export_url(spreadsheet_id, gid=gid)
        output_path = RAW_OUTPUT_DIR / f"{name}_gid{gid}_preview.csv"

        print(f"Inspecting {name}: {spreadsheet_id} gid={gid}")
        try:
            text = download_text(url)
        except Exception as exc:
            errors.append(f"{name}: download failed: {exc}")
            continue

        if looks_like_html(text):
            errors.append(f"{name}: downloaded content looks like HTML. Check Google Sheets sharing settings.")
            continue

        header, row_count = inspect_csv_text(text)
        if not header:
            errors.append(f"{name}: CSV appears to be empty")
            continue

        output_path.write_text(text, encoding="utf-8")
        print(f"  saved: {output_path}")
        print(f"  rows: {row_count}")
        print(f"  columns: {header}")

    if errors:
        print("Google Sheets history source inspection: FAILED")
        for error in errors:
            print("ERROR: " + error)
        raise SystemExit(1)

    print("Google Sheets history source inspection: OK")
    print("STEP 102 CHECK: OK")


if __name__ == "__main__":
    main()
