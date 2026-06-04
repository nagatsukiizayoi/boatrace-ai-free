#!/usr/bin/env python3
import json
from pathlib import Path

CONFIG_PATH = Path("data/history_sources.json")

REQUIRED_TOP_LEVEL_KEYS = [
    "version",
    "description",
    "csv_partition",
    "race_id",
    "google_sheets",
    "official_sources",
    "yearly_csv_outputs",
    "database",
    "required_common_columns",
    "initial_implementation_steps",
]

REQUIRED_GOOGLE_SHEET_IDS = [
    "1RteBnvLCXaLi5brLHgZhxGBOY6blfLYTPfRTcxlatwM",
    "1XhurwQfrBdtvTRiTJx_n6MvC4ftqbPvLUr6ip1Pp3rE",
    "1n50JSqeqnYwOPMM5grT8GjGmYc-rV6qQZFLSdRR17rI",
    "1YY2FhdWWUf9RV4e1gqu4qAadEtMD8qB_Bw6ejrGICOo",
]

REQUIRED_YEARLY_OUTPUTS = [
    "races",
    "race_entries",
    "odds",
    "results",
    "predictions",
    "bet_results",
    "racer_term_stats",
]

REQUIRED_DIRECTORIES = [
    "data/raw/boatrace_official/results",
    "data/raw/boatrace_official/programs",
    "data/raw/boatrace_official/racer_term_stats",
    "data/raw/google_sheets",
    "data/import/history/races",
    "data/import/history/race_entries",
    "data/import/history/odds",
    "data/import/history/results",
    "data/import/history/predictions",
    "data/import/history/bet_results",
    "data/import/history/racer_term_stats",
    "data/import/google_sheets",
]


def main():
    errors = []

    if not CONFIG_PATH.exists():
        errors.append("missing file: data/history_sources.json")
    else:
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append("invalid JSON: " + str(exc))
            data = {}

        for key in REQUIRED_TOP_LEVEL_KEYS:
            if key not in data:
                errors.append("missing top-level key: " + key)

        google_sheets = data.get("google_sheets", [])
        if not isinstance(google_sheets, list):
            errors.append("google_sheets must be a list")
            google_sheets = []

        found_ids = [str(item.get("spreadsheet_id", "")) for item in google_sheets if isinstance(item, dict)]
        for sheet_id in REQUIRED_GOOGLE_SHEET_IDS:
            if sheet_id not in found_ids:
                errors.append("missing Google Sheets spreadsheet_id: " + sheet_id)

        if len(google_sheets) < 4:
            errors.append("google_sheets must contain at least 4 entries")

        race_id = data.get("race_id", {})
        if not isinstance(race_id, dict):
            errors.append("race_id must be an object")
        else:
            if race_id.get("format") != "YYYYMMDD-venue_code-race_no":
                errors.append("race_id.format mismatch")
            if race_id.get("required") is not True:
                errors.append("race_id.required must be true")

        csv_partition = data.get("csv_partition", {})
        if not isinstance(csv_partition, dict):
            errors.append("csv_partition must be an object")
        else:
            if csv_partition.get("unit") != "year":
                errors.append("csv_partition.unit must be year")
            if csv_partition.get("enabled") is not True:
                errors.append("csv_partition.enabled must be true")

        outputs = data.get("yearly_csv_outputs", {})
        if not isinstance(outputs, dict):
            errors.append("yearly_csv_outputs must be an object")
        else:
            for key in REQUIRED_YEARLY_OUTPUTS:
                value = outputs.get(key)
                if not value:
                    errors.append("missing yearly_csv_outputs key: " + key)
                elif "{year}" not in value:
                    errors.append("yearly_csv_outputs must contain {year}: " + key)

        database = data.get("database", {})
        if not isinstance(database, dict):
            errors.append("database must be an object")
        else:
            if database.get("path") != "db/boatrace.sqlite3":
                errors.append("database.path must be db/boatrace.sqlite3")

        required_common_columns = data.get("required_common_columns", [])
        for column in ["race_id", "race_date", "venue_code", "venue_name", "race_no"]:
            if column not in required_common_columns:
                errors.append("missing required_common_columns: " + column)

    for directory in REQUIRED_DIRECTORIES:
        if not Path(directory).is_dir():
            errors.append("missing directory: " + directory)

    if errors:
        print("History sources config validation: FAILED")
        for error in errors:
            print("ERROR: " + error)
        raise SystemExit(1)

    print("History sources config validation: OK")
    print("STEP 101 CHECK: OK")


if __name__ == "__main__":
    main()
