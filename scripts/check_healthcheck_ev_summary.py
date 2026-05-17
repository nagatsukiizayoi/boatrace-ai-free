#!/usr/bin/env python3
import json
import sys
from pathlib import Path


HEALTHCHECK_PATH = Path("docs/healthcheck.html")
PREDICTION_JSON_PATH = Path("docs/prediction.json")


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def to_float(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def main() -> None:
    if not HEALTHCHECK_PATH.exists():
        fail("docs/healthcheck.html does not exist")

    if not PREDICTION_JSON_PATH.exists():
        fail("docs/prediction.json does not exist")

    html = HEALTHCHECK_PATH.read_text(encoding="utf-8")

    required_tokens = [
        "STEP86_EV_HEALTHCHECK_STYLE",
        "STEP86_EV_HEALTHCHECK_HTML",
        "STEP86_EV_HEALTHCHECK_SCRIPT",
        "expected_value",
        "odds",
    ]

    missing_tokens = [token for token in required_tokens if token not in html]
    if missing_tokens:
        fail(f"Missing healthcheck tokens: {missing_tokens}")

    print("Healthcheck STEP86 markers: OK")

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
    ]

    missing_top = [key for key in required_top_keys if key not in data]
    if missing_top:
        fail(f"Missing top-level keys: {missing_top}")

    races = data.get("races", [])
    alerts = data.get("alerts", [])

    if not isinstance(races, list) or not races:
        fail("races must be a non-empty list")

    if not isinstance(alerts, list):
        fail("alerts must be a list")

    recommendations = []

    for race in races:
        race_no = race.get("race_no")
        venue_name = race.get("venue_name") or race.get("venue") or ""
        for rec in race.get("recommendations", []):
            recommendations.append(
                {
                    "race_no": race_no,
                    "venue_name": venue_name,
                    "rec": rec,
                }
            )

    if not recommendations:
        fail("No recommendations found in prediction.json")

    odds_count = 0
    ev_count = 0
    high_ev_count = 0
    max_odds = 0.0
    max_ev = 0.0
    high_ev_items = []

    for item in recommendations:
        rec = item["rec"]

        odds = to_float(rec.get("odds"))
        ev = to_float(rec.get("expected_value"))

        if odds > 0:
            odds_count += 1
            max_odds = max(max_odds, odds)

        if ev > 0:
            ev_count += 1
            max_ev = max(max_ev, ev)

        if ev >= 1.2:
            high_ev_count += 1
            high_ev_items.append(
                {
                    "race_no": item["race_no"],
                    "venue_name": item["venue_name"],
                    "bet_type": rec.get("bet_type"),
                    "combination": rec.get("combination"),
                    "odds": odds,
                    "expected_value": ev,
                }
            )

    expected_value_alert_count = 0

    for alert in alerts:
        text = json.dumps(alert, ensure_ascii=False)
        if "期待値" in text or "expected_value" in text or "EV" in text:
            expected_value_alert_count += 1

    print("races:", len(races))
    print("alerts:", len(alerts))
    print("recommendations:", len(recommendations))
    print("odds_count:", odds_count)
    print("ev_count:", ev_count)
    print("high_ev_count:", high_ev_count)
    print("expected_value_alert_count:", expected_value_alert_count)
    print("max_odds:", max_odds)
    print("max_ev:", max_ev)

    if odds_count < 1:
        fail("No recommendation with odds > 0")

    if ev_count < 1:
        fail("No recommendation with expected_value > 0")

    if high_ev_count < 1:
        fail("No recommendation with expected_value >= 1.2")

    if expected_value_alert_count < 1:
        fail("No expected value alert found in alerts")

    print("High EV preview:")
    for item in high_ev_items[:10]:
        print(
            f'{item["race_no"]}R',
            item["bet_type"],
            item["combination"],
            "odds=", item["odds"],
            "EV=", item["expected_value"],
        )

    print("Prediction JSON EV data: OK")
    print("STEP 87 CHECK: OK")


if __name__ == "__main__":
    main()
