#!/usr/bin/env python3
import json
import sys
from pathlib import Path


PREDICTION_JSON_PATH = Path("docs/prediction.json")
ENRICH_SCRIPT_PATH = Path("scripts/enrich_recommendation_reasons.py")

EXPECTED_REASON_VERSION = "recommendation_reason_v1"


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if not PREDICTION_JSON_PATH.exists():
        fail("docs/prediction.json does not exist")

    if not ENRICH_SCRIPT_PATH.exists():
        fail("scripts/enrich_recommendation_reasons.py does not exist")

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
        fail(f"Missing top-level keys: {missing_top}")

    reasoning = data.get("recommendation_reasoning")
    if not isinstance(reasoning, dict):
        fail("recommendation_reasoning must be an object")

    if reasoning.get("enabled") is not True:
        fail("recommendation_reasoning.enabled must be true")

    version = reasoning.get("version")
    if version != EXPECTED_REASON_VERSION:
        fail(f"recommendation_reasoning.version must be {EXPECTED_REASON_VERSION}, got {version}")

    races = data.get("races", [])
    if not isinstance(races, list) or not races:
        fail("races must be a non-empty list")

    total_recommendations = 0
    with_reason = 0
    with_points = 0
    with_grade = 0
    with_risk_note = 0
    with_reason_version = 0

    grade_counts = {}

    missing_items = []

    for race_index, race in enumerate(races):
        race_no = race.get("race_no") or race.get("race_number") or f"index-{race_index}"
        recommendations = race.get("recommendations", [])

        if not isinstance(recommendations, list):
            fail(f"race {race_no} recommendations must be a list")

        for rec_index, rec in enumerate(recommendations):
            if not isinstance(rec, dict):
                fail(f"race {race_no} recommendation {rec_index} must be an object")

            total_recommendations += 1

            label = f"race={race_no} rec_index={rec_index} bet_type={rec.get('bet_type')} combination={rec.get('combination')}"

            recommendation_reason = rec.get("recommendation_reason")
            reason_points = rec.get("reason_points")
            value_grade = rec.get("value_grade")
            risk_note = rec.get("risk_note")
            reason_version = rec.get("reason_version")

            if isinstance(recommendation_reason, str) and recommendation_reason.strip():
                with_reason += 1
            else:
                missing_items.append(f"{label}: missing recommendation_reason")

            if isinstance(reason_points, list) and len(reason_points) >= 2:
                if all(isinstance(p, str) and p.strip() for p in reason_points):
                    with_points += 1
                else:
                    missing_items.append(f"{label}: reason_points contains empty/non-string item")
            else:
                missing_items.append(f"{label}: missing reason_points or too few points")

            if isinstance(value_grade, str) and value_grade.strip():
                with_grade += 1
                grade_counts[value_grade] = grade_counts.get(value_grade, 0) + 1
            else:
                missing_items.append(f"{label}: missing value_grade")

            if isinstance(risk_note, str) and risk_note.strip():
                with_risk_note += 1
            else:
                missing_items.append(f"{label}: missing risk_note")

            if reason_version == EXPECTED_REASON_VERSION:
                with_reason_version += 1
            else:
                missing_items.append(f"{label}: invalid reason_version={reason_version}")

    if total_recommendations == 0:
        fail("No recommendations found")

    print("recommendation_reasoning:", reasoning)
    print("total_recommendations:", total_recommendations)
    print("with_reason:", with_reason)
    print("with_points:", with_points)
    print("with_grade:", with_grade)
    print("with_risk_note:", with_risk_note)
    print("with_reason_version:", with_reason_version)
    print("grade_counts:", grade_counts)

    if missing_items:
        print("Missing/invalid recommendation reason fields:")
        for item in missing_items[:50]:
            print("-", item)
        fail(f"{len(missing_items)} recommendation reason validation errors found")

    expected_total = reasoning.get("total_recommendations")
    enriched_total = reasoning.get("enriched_recommendations")

    if expected_total is not None and int(expected_total) != total_recommendations:
        fail(
            f"recommendation_reasoning.total_recommendations mismatch: "
            f"{expected_total} != {total_recommendations}"
        )

    if enriched_total is not None and int(enriched_total) != total_recommendations:
        fail(
            f"recommendation_reasoning.enriched_recommendations mismatch: "
            f"{enriched_total} != {total_recommendations}"
        )

    print("Recommendation reason validation: OK")
    print("STEP 91 CHECK: OK")


if __name__ == "__main__":
    main()
