#!/usr/bin/env python3
import json
import sys
from collections import defaultdict
from pathlib import Path


INDEX_PATH = Path("docs/index.html")
PREDICTION_JSON_PATH = Path("docs/prediction.json")

EXPECTED_REASON_VERSION = "recommendation_reason_v1"
HIGH_EV_THRESHOLD = 1.2


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
        "STEP94_GROUPED_RECOMMENDATION_REASONS_STYLE",
        "STEP94_GROUPED_RECOMMENDATION_REASONS_HTML",
        "STEP94_GROUPED_RECOMMENDATION_REASONS_SCRIPT",
        "step94GroupedRecommendationReasonsPanel",
        "step94GroupedRecommendationReasonsStatus",
        "step94GroupedRecommendationReasonsList",
        "step94LoadGroupedRecommendationReasons",
        "recommendation_reason",
        "reason_points",
        "value_grade",
        "risk_note",
        "レース別 推奨理由サマリー",
    ]

    missing_index_tokens = [token for token in required_index_tokens if token not in html]
    if missing_index_tokens:
        fail(f"Missing STEP94 grouped reason panel tokens: {missing_index_tokens}")

    print("Dashboard STEP94 grouped recommendation reason panel markers: OK")

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
        "recommendation_reasoning",
    ]

    missing_top = [key for key in required_top_keys if key not in data]
    if missing_top:
        fail(f"Missing top-level keys in prediction.json: {missing_top}")

    reasoning = data.get("recommendation_reasoning")
    if not isinstance(reasoning, dict):
        fail("recommendation_reasoning must be an object")

    if reasoning.get("enabled") is not True:
        fail("recommendation_reasoning.enabled must be true")

    if reasoning.get("version") != EXPECTED_REASON_VERSION:
        fail(
            f"recommendation_reasoning.version must be {EXPECTED_REASON_VERSION}, "
            f"got {reasoning.get('version')}"
        )

    races = data.get("races", [])
    if not isinstance(races, list) or not races:
        fail("races must be a non-empty list")

    grouped = defaultdict(list)

    total_recommendations = 0
    with_reason = 0
    with_points = 0
    high_ev_count = 0
    max_ev = 0.0
    max_odds = 0.0
    errors = []

    for race_index, race in enumerate(races):
        race_no = race.get("race_no") or race.get("race_number") or f"index-{race_index}"
        venue_name = race.get("venue_name") or race.get("venue") or ""
        recommendations = race.get("recommendations", [])

        if not isinstance(recommendations, list):
            fail(f"race {race_no} recommendations must be a list")

        for rec_index, rec in enumerate(recommendations):
            if not isinstance(rec, dict):
                fail(f"race {race_no} recommendation {rec_index} must be an object")

            total_recommendations += 1

            label = (
                f"race={race_no} "
                f"rec_index={rec_index} "
                f"bet_type={rec.get('bet_type')} "
                f"combination={rec.get('combination')}"
            )

            reason = rec.get("recommendation_reason")
            points = rec.get("reason_points")
            grade = rec.get("value_grade")
            risk_note = rec.get("risk_note")
            reason_version = rec.get("reason_version")

            ev = to_float(rec.get("expected_value"))
            odds = to_float(rec.get("odds"))

            max_ev = max(max_ev, ev)
            max_odds = max(max_odds, odds)

            if ev >= HIGH_EV_THRESHOLD:
                high_ev_count += 1

            if isinstance(reason, str) and reason.strip():
                with_reason += 1
            else:
                errors.append(f"{label}: missing recommendation_reason")

            if isinstance(points, list) and len(points) >= 2:
                with_points += 1
            else:
                errors.append(f"{label}: missing reason_points or too few points")

            if not isinstance(grade, str) or not grade.strip():
                errors.append(f"{label}: missing value_grade")

            if not isinstance(risk_note, str) or not risk_note.strip():
                errors.append(f"{label}: missing risk_note")

            if reason_version != EXPECTED_REASON_VERSION:
                errors.append(f"{label}: invalid reason_version={reason_version}")

            grouped[str(race_no)].append(
                {
                    "race_no": race_no,
                    "venue_name": venue_name,
                    "bet_type": rec.get("bet_type"),
                    "combination": rec.get("combination"),
                    "expected_value": ev,
                    "odds": odds,
                    "value_grade": grade,
                    "recommendation_reason": reason,
                }
            )

    if total_recommendations == 0:
        fail("No recommendations found")

    if not grouped:
        fail("No grouped recommendations found")

    if high_ev_count < 1:
        errors.append(f"No high EV recommendation expected_value >= {HIGH_EV_THRESHOLD}")

    grouped_race_count = len(grouped)

    print("recommendation_reasoning:", reasoning)
    print("races:", len(races))
    print("grouped_race_count:", grouped_race_count)
    print("total_recommendations:", total_recommendations)
    print("with_reason:", with_reason)
    print("with_points:", with_points)
    print("high_ev_count:", high_ev_count)
    print("max_ev:", max_ev)
    print("max_odds:", max_odds)

    print("Grouped race preview:")
    for race_no, items in sorted(grouped.items(), key=lambda x: str(x[0]))[:10]:
        race_high_ev = [item for item in items if item["expected_value"] >= HIGH_EV_THRESHOLD]
        race_max_ev = max((item["expected_value"] for item in items), default=0.0)
        race_max_odds = max((item["odds"] for item in items), default=0.0)
        print(
            f"{race_no}R",
            "recommendations=", len(items),
            "high_ev=", len(race_high_ev),
            "max_ev=", race_max_ev,
            "max_odds=", race_max_odds,
        )

    expected_total = reasoning.get("total_recommendations")
    enriched_total = reasoning.get("enriched_recommendations")

    if expected_total is not None and int(expected_total) != total_recommendations:
        errors.append(
            f"recommendation_reasoning.total_recommendations mismatch: "
            f"{expected_total} != {total_recommendations}"
        )

    if enriched_total is not None and int(enriched_total) != total_recommendations:
        errors.append(
            f"recommendation_reasoning.enriched_recommendations mismatch: "
            f"{enriched_total} != {total_recommendations}"
        )

    if errors:
        print("Validation errors:")
        for e in errors[:100]:
            print("-", e)
        fail(f"{len(errors)} validation errors found")

    print("Grouped recommendation reasons validation: OK")
    print("STEP 95 CHECK: OK")


if __name__ == "__main__":
    main()
