#!/usr/bin/env python3
import json
import sys
from pathlib import Path


INDEX_PATH = Path("docs/index.html")
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
    if not INDEX_PATH.exists():
        fail("docs/index.html does not exist")

    if not PREDICTION_JSON_PATH.exists():
        fail("docs/prediction.json does not exist")

    html = INDEX_PATH.read_text(encoding="utf-8")

    required_index_tokens = [
        "STEP88_EV_SUMMARY_CARDS_STYLE",
        "STEP88_EV_SUMMARY_CARDS_HTML",
        "STEP88_EV_SUMMARY_CARDS_SCRIPT",
        "step88EvSummaryPanel",
        "step88EvSummaryStatus",
        "step88TotalRecommendations",
        "step88HighEvCount",
        "step88MaxEv",
        "step88MaxOdds",
        "step88OddsCount",
        "step88EvCount",
        "step88ExpectedValueAlerts",
        "step88RaceCount",
        "EVサマリー",
        "expected_value",
        "odds",
    ]

    missing_index_tokens = [token for token in required_index_tokens if token not in html]
    if missing_index_tokens:
        fail(f"Missing STEP88 dashboard tokens: {missing_index_tokens}")

    print("Dashboard STEP88 EV summary markers: OK")

    try:
        data = json.loads(PREDICTION_JSON_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        fail(f"Invalid docs/prediction.json: {e}")

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
        fail(f"Missing top-level keys in prediction.json: {missing_top}")

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
        recs = race.get("recommendations", [])

        if not isinstance(recs, list):
            fail(f"race {race_no} recommendations must be a list")

        for rec in recs:
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
    max_odds_item = None
    max_ev_item = None
    high_ev_items = []

    for item in recommendations:
        rec = item["rec"]

        odds = to_float(rec.get("odds"))
        ev = to_float(rec.get("expected_value"))

        if odds > 0:
            odds_count += 1
            if odds > max_odds:
                max_odds = odds
                max_odds_item = item

        if ev > 0:
            ev_count += 1
            if ev > max_ev:
                max_ev = ev
                max_ev_item = item

        if ev >= 1.2:
            high_ev_count += 1
            high_ev_items.append(item)

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
        rec = item["rec"]
        print(
            f'{item["race_no"]}R',
            rec.get("bet_type"),
            rec.get("combination"),
            "odds=", rec.get("odds"),
            "EV=", rec.get("expected_value"),
        )

    if max_ev_item:
        rec = max_ev_item["rec"]
        print(
            "Max EV ticket:",
            f'{max_ev_item["race_no"]}R',
            rec.get("bet_type"),
            rec.get("combination"),
            "EV=", rec.get("expected_value"),
        )

    if max_odds_item:
        rec = max_odds_item["rec"]
        print(
            "Max odds ticket:",
            f'{max_odds_item["race_no"]}R',
            rec.get("bet_type"),
            rec.get("combination"),
            "odds=", rec.get("odds"),
        )

    print("Dashboard EV summary card validation: OK")
    print("STEP 89 CHECK: OK")


if __name__ == "__main__":
    main()
