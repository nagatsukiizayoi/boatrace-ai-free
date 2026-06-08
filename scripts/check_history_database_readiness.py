#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

CHECKS = [
    ["python", "scripts/check_history_sources_config.py"],
    ["python", "scripts/check_google_sheets_history_profile.py"],
    ["python", "scripts/check_google_sheets_column_mapping.py"],
    ["python", "scripts/check_history_results_csv.py"],
    ["python", "scripts/check_history_database.py"],
    ["python", "scripts/check_history_database_summary.py"],
    ["python", "scripts/check_racer_history_features.py"],
    ["python", "scripts/check_racer_history_features_summary.py"],
    ["python", "scripts/check_history_feature_config.py"],
    ["python", "scripts/check_history_feature_loader.py"],
    ["python", "scripts/check_prediction_history_feature_join.py"],
    ["python", "scripts/check_dashboard_history_feature_summary.py"],
]

REQUIRED_FILES = [
    "data/history_sources.json",
    "data/google_sheets_column_mapping.json",
    "data/import/google_sheets/google_sheets_history_profile.json",
    "data/import/history/history_database_summary.json",
    "docs/history_database_summary.json",
    "scripts/build_history_database.py",
    "scripts/export_history_database_summary.py",
    "scripts/build_racer_history_features.py",
    "scripts/check_racer_history_features.py",
    "data/import/history/racer_history_features.csv",
    "scripts/export_racer_history_features_summary.py",
    "scripts/check_racer_history_features_summary.py",
    "docs/racer_history_features_summary.json",
    "docs/index.html",
    "data/history_feature_config.json",
    "scripts/check_history_feature_config.py",
    "scripts/history_feature_loader.py",
    "scripts/check_history_feature_loader.py",
    "scripts/check_prediction_history_feature_join.py",
    "scripts/check_dashboard_history_feature_summary.py",
]

REQUIRED_RESULT_CSV_GLOB = "data/import/history/results/results_*.csv"


def main():
    errors = []

    for path in REQUIRED_FILES:
        if not Path(path).exists():
            errors.append(f"missing required file: {path}")

    result_files = sorted(Path("data/import/history/results").glob("results_*.csv"))
    if not result_files:
        errors.append(f"missing result CSV files: {REQUIRED_RESULT_CSV_GLOB}")

    if errors:
        print("History database readiness validation: FAILED")
        for error in errors:
            print("ERROR: " + error)
        raise SystemExit(1)

    for command in CHECKS:
        print("$ " + " ".join(command))
        completed = subprocess.run(command)
        if completed.returncode != 0:
            print("History database readiness validation: FAILED")
            print("ERROR: command failed: " + " ".join(command))
            raise SystemExit(completed.returncode)

    print("History database readiness validation: OK")
    print("STEP 112 CHECK: OK")


if __name__ == "__main__":
    main()
