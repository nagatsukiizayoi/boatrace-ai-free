#!/usr/bin/env python3
import json
from pathlib import Path

INDEX_PATH = Path("docs/index.html")
HISTORY_DB_SUMMARY_PATH = Path("docs/history_database_summary.json")
RACER_FEATURE_SUMMARY_PATH = Path("docs/racer_history_features_summary.json")

def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"invalid JSON: {path}: {exc}")

def main():
    errors = []

    if not INDEX_PATH.exists():
        errors.append(f"missing file: {INDEX_PATH}")
    else:
        html = INDEX_PATH.read_text(encoding="utf-8")
        required_fragments = [
            "history-feature-summary-section",
            "history_database_summary.json",
            "racer_history_features_summary.json",
            "履歴DB・履歴特徴量サマリー",
            "enabled:false",
            "hfs-db-total-rows",
            "hfs-racer-count",
            "hfs-top-race-count",
            "hfs-top-win-rate",
            "hfs-top-top3-rate",
        ]
        for fragment in required_fragments:
            if fragment not in html:
                errors.append(f"docs/index.html missing fragment: {fragment}")

    if not HISTORY_DB_SUMMARY_PATH.exists():
        errors.append(f"missing file: {HISTORY_DB_SUMMARY_PATH}")
    else:
        db = load_json(HISTORY_DB_SUMMARY_PATH)
        for key in ["total_rows", "total_races", "venue_count", "racer_count"]:
            if key not in db:
                errors.append(f"{HISTORY_DB_SUMMARY_PATH} missing key: {key}")
        if int(db.get("total_rows", 0) or 0) <= 0:
            errors.append("history database total_rows must be positive")
        if int(db.get("total_races", 0) or 0) <= 0:
            errors.append("history database total_races must be positive")

    if not RACER_FEATURE_SUMMARY_PATH.exists():
        errors.append(f"missing file: {RACER_FEATURE_SUMMARY_PATH}")
    else:
        racer = load_json(RACER_FEATURE_SUMMARY_PATH)
        if int(racer.get("racer_count", 0) or 0) <= 0:
            errors.append("racer feature summary racer_count must be positive")
        if int(racer.get("total_race_count", 0) or 0) <= 0:
            errors.append("racer feature summary total_race_count must be positive")

        ranking_keys = [
            "top_racers_by_race_count",
            "top_by_race_count",
            "top_race_count",
        ]
        if not any(isinstance(racer.get(k), list) for k in ranking_keys):
            errors.append("racer feature summary missing race count ranking array")

    if errors:
        print("Dashboard history feature summary validation: FAILED")
        for e in errors:
            print("ERROR: " + e)
        raise SystemExit(1)

    print("Dashboard history feature summary validation: OK")
    print("STEP 129-A CHECK: OK")

if __name__ == "__main__":
    main()
