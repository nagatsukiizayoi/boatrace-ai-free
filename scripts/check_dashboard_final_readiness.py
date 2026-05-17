#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


INDEX_PATH = Path("docs/index.html")
HEALTHCHECK_PATH = Path("docs/healthcheck.html")
PREDICTION_JSON_PATH = Path("docs/prediction.json")


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def run_check(command: list[str]) -> None:
    print("Running:", " ".join(command))
    result = subprocess.run(command, text=True)
    if result.returncode != 0:
        fail(f"Command failed: {' '.join(command)}")


def require_file(path: Path) -> None:
    if not path.exists():
        fail(f"Required file missing: {path}")
    print(f"File exists: {path}")


def require_tokens(path: Path, tokens: list[str], label: str) -> None:
    text = path.read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in text]
    if missing:
        fail(f"{label} missing tokens: {missing}")
    print(f"{label} tokens: OK")


def validate_prediction_json() -> None:
    try:
        data = json.loads(PREDICTION_JSON_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        fail(f"Invalid prediction.json: {e}")

    required_top_keys = [
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

    missing = [key for key in required_top_keys if key not in data]
    if missing:
        fail(f"prediction.json missing top-level keys: {missing}")

    races = data.get("races", [])
    alerts = data.get("alerts", [])
    reasoning = data.get("recommendation_reasoning", {})

    if not isinstance(races, list) or not races:
        fail("prediction.json races must be a non-empty list")

    if not isinstance(alerts, list):
        fail("prediction.json alerts must be a list")

    if not isinstance(reasoning, dict) or reasoning.get("enabled") is not True:
        fail("recommendation_reasoning.enabled must be true")

    recommendations = []
    for race in races:
        for rec in race.get("recommendations", []):
            recommendations.append(rec)

    if not recommendations:
        fail("No recommendations found")

    odds_count = 0
    ev_count = 0
    high_ev_count = 0
    reason_count = 0
    points_count = 0
    risk_count = 0

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

        if isinstance(rec.get("reason_points"), list) and len(rec["reason_points"]) >= 2:
            points_count += 1

        if isinstance(rec.get("risk_note"), str) and rec["risk_note"].strip():
            risk_count += 1

    alert_text = json.dumps(alerts, ensure_ascii=False)
    expected_value_alert_count = sum(
        1
        for alert in alerts
        if "期待値" in json.dumps(alert, ensure_ascii=False)
        or "expected_value" in json.dumps(alert, ensure_ascii=False)
        or "EV" in json.dumps(alert, ensure_ascii=False)
    )

    print("prediction.json summary:")
    print("races:", len(races))
    print("alerts:", len(alerts))
    print("recommendations:", len(recommendations))
    print("odds_count:", odds_count)
    print("ev_count:", ev_count)
    print("high_ev_count:", high_ev_count)
    print("reason_count:", reason_count)
    print("points_count:", points_count)
    print("risk_count:", risk_count)
    print("expected_value_alert_count:", expected_value_alert_count)

    errors = []

    if odds_count < 1:
        errors.append("No recommendations with odds > 0")
    if ev_count < 1:
        errors.append("No recommendations with expected_value > 0")
    if high_ev_count < 1:
        errors.append("No high EV recommendations expected_value >= 1.2")
    if expected_value_alert_count < 1:
        errors.append("No expected value alerts")
    if reason_count != len(recommendations):
        errors.append(f"Not all recommendations have recommendation_reason: {reason_count}/{len(recommendations)}")
    if points_count != len(recommendations):
        errors.append(f"Not all recommendations have reason_points: {points_count}/{len(recommendations)}")
    if risk_count != len(recommendations):
        errors.append(f"Not all recommendations have risk_note: {risk_count}/{len(recommendations)}")

    if errors:
        for e in errors:
            print("-", e)
        fail(f"{len(errors)} prediction.json validation errors found")

    print("prediction.json final validation: OK")


def main() -> None:
    print("STEP 100 final dashboard readiness check")

    require_file(INDEX_PATH)
    require_file(HEALTHCHECK_PATH)
    require_file(PREDICTION_JSON_PATH)

    index_tokens = [
        "STEP82_EXPECTED_VALUE_ALERT",
        "STEP84_EV_TICKET_BADGE",
        "STEP88_EV_SUMMARY_CARDS",
        "STEP92_RECOMMENDATION_REASONS",
        "STEP94_GROUPED_RECOMMENDATION_REASONS",
        "STEP98_QUALITY_SCORE_CARDS",
        "期待値アラート",
        "EVサマリー",
        "買い目別 推奨理由",
        "レース別 推奨理由サマリー",
        "予想データ品質スコア",
    ]

    healthcheck_tokens = [
        "STEP86_EV_HEALTHCHECK",
        "STEP96_RECOMMENDATION_REASON_HEALTHCHECK",
        "推奨理由 Health Check",
    ]

    require_tokens(INDEX_PATH, index_tokens, "docs/index.html")
    require_tokens(HEALTHCHECK_PATH, healthcheck_tokens, "docs/healthcheck.html")

    validate_prediction_json()

    existing_checks = [
        ["python", "scripts/check_recommendation_reasons.py"],
        ["python", "scripts/check_grouped_recommendation_reasons.py"],
        ["python", "scripts/check_healthcheck_recommendation_reason_summary.py"],
        ["python", "scripts/check_dashboard_quality_score_cards.py"],
    ]

    for command in existing_checks:
        script_path = Path(command[1])
        require_file(script_path)
        run_check(command)

    print("Dashboard final readiness validation: OK")
    print("STEP 100 CHECK: OK")


if __name__ == "__main__":
    main()
