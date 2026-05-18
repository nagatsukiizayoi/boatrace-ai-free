#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


PYTHON = sys.executable

PREDICTION_JSON_PATH = Path("docs/prediction.json")


def run(command: list[str]) -> None:
    print("")
    print("=" * 80)
    print("RUN:", " ".join(command))
    print("=" * 80)

    result = subprocess.run(command)

    if result.returncode != 0:
        raise SystemExit(f"Command failed with exit code {result.returncode}: {' '.join(command)}")


def require_file(path: str) -> None:
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"Required file missing: {path}")
    print(f"Required file exists: {path}")


def validate_prediction_json() -> None:
    if not PREDICTION_JSON_PATH.exists():
        raise SystemExit("docs/prediction.json does not exist")

    try:
        data = json.loads(PREDICTION_JSON_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"Invalid docs/prediction.json: {e}")

    required = [
        "updated_at",
        "run_key",
        "model_name",
        "model_version",
        "target_date",
        "summary",
        "races",
        "alerts",
        "recommendation_reasoning",
    ]

    missing = [key for key in required if key not in data]
    if missing:
        raise SystemExit(f"Missing top-level keys in prediction.json: {missing}")

    races = data.get("races", [])
    alerts = data.get("alerts", [])

    if not isinstance(races, list) or not races:
        raise SystemExit("prediction.json races must be a non-empty list")

    if not isinstance(alerts, list):
        raise SystemExit("prediction.json alerts must be a list")

    recommendations = []

    for race in races:
        recs = race.get("recommendations", [])
        if isinstance(recs, list):
            recommendations.extend(recs)

    if not recommendations:
        raise SystemExit("No recommendations found in prediction.json")

    odds_count = 0
    ev_count = 0
    high_ev_count = 0
    reason_count = 0

    for rec in recommendations:
        try:
            odds = float(rec.get("odds") or 0)
        except (TypeError, ValueError):
            odds = 0.0

        try:
            ev = float(rec.get("expected_value") or 0)
        except (TypeError, ValueError):
            ev = 0.0

        if odds > 0:
            odds_count += 1

        if ev > 0:
            ev_count += 1

        if ev >= 1.2:
            high_ev_count += 1

        if isinstance(rec.get("recommendation_reason"), str) and rec["recommendation_reason"].strip():
            reason_count += 1

    print("")
    print("prediction.json pipeline summary:")
    print("races:", len(races))
    print("alerts:", len(alerts))
    print("recommendations:", len(recommendations))
    print("odds_count:", odds_count)
    print("ev_count:", ev_count)
    print("high_ev_count:", high_ev_count)
    print("reason_count:", reason_count)

    if odds_count < 1:
        raise SystemExit("No odds-applied recommendations found")

    if ev_count < 1:
        raise SystemExit("No expected_value recommendations found")

    if high_ev_count < 1:
        raise SystemExit("No high EV recommendations found")

    if reason_count != len(recommendations):
        raise SystemExit(f"Not all recommendations have recommendation_reason: {reason_count}/{len(recommendations)}")

    print("prediction.json validation: OK")


def main() -> None:
    print("STEP 101 full prediction pipeline")

    required_files = [
        "db/schema.sql",
        "data/import/races.csv",
        "data/import/race_entries.csv",
        "data/import/odds.csv",
        "docs/index.html",
        "docs/healthcheck.html",
        "scripts/init_db.py",
        "scripts/import_race_csv.py",
        "scripts/import_odds_csv.py",
        "scripts/generate_simple_predictions.py",
        "scripts/apply_odds_to_predictions.py",
        "scripts/create_expected_value_alerts.py",
        "scripts/export_prediction_json.py",
        "scripts/enrich_prediction_json.py",
        "scripts/enrich_recommendation_reasons.py",
        "scripts/check_recommendation_reasons.py",
        "scripts/check_grouped_recommendation_reasons.py",
        "scripts/check_healthcheck_recommendation_reason_summary.py",
        "scripts/check_dashboard_quality_score_cards.py",
        "scripts/check_dashboard_final_readiness.py",
    ]

    for file in required_files:
        require_file(file)

    scripts_to_compile = [
        "scripts/init_db.py",
        "scripts/import_race_csv.py",
        "scripts/import_odds_csv.py",
        "scripts/generate_simple_predictions.py",
        "scripts/apply_odds_to_predictions.py",
        "scripts/create_expected_value_alerts.py",
        "scripts/export_prediction_json.py",
        "scripts/enrich_prediction_json.py",
        "scripts/enrich_recommendation_reasons.py",
        "scripts/check_recommendation_reasons.py",
        "scripts/check_grouped_recommendation_reasons.py",
        "scripts/check_healthcheck_recommendation_reason_summary.py",
        "scripts/check_dashboard_quality_score_cards.py",
        "scripts/check_dashboard_final_readiness.py",
    ]

    for script in scripts_to_compile:
        run([PYTHON, "-m", "py_compile", script])

    pipeline_commands = [
        [PYTHON, "scripts/init_db.py", "--reset"],
        [PYTHON, "scripts/import_race_csv.py"],
        [PYTHON, "scripts/import_odds_csv.py"],
        [PYTHON, "scripts/generate_simple_predictions.py"],
        [PYTHON, "scripts/apply_odds_to_predictions.py"],
        [PYTHON, "scripts/create_expected_value_alerts.py"],
        [PYTHON, "scripts/export_prediction_json.py"],
        [PYTHON, "scripts/enrich_prediction_json.py"],
        [PYTHON, "scripts/enrich_recommendation_reasons.py"],
    ]

    for command in pipeline_commands:
        run(command)

    validate_prediction_json()

    check_commands = [
        [PYTHON, "scripts/check_recommendation_reasons.py"],
        [PYTHON, "scripts/check_grouped_recommendation_reasons.py"],
        [PYTHON, "scripts/check_healthcheck_recommendation_reason_summary.py"],
        [PYTHON, "scripts/check_dashboard_quality_score_cards.py"],
        [PYTHON, "scripts/check_dashboard_final_readiness.py"],
    ]

    for command in check_commands:
        run(command)

    print("")
    print("Full prediction pipeline validation: OK")
    print("STEP 101 CHECK: OK")


if __name__ == "__main__":
    main()
