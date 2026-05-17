#!/usr/bin/env python3
import json
import sys
from pathlib import Path


HEALTHCHECK_PATH = Path("docs/healthcheck.html")
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
    if not HEALTHCHECK_PATH.exists():
        fail("docs/healthcheck.html does not exist")

    if not PREDICTION_JSON_PATH.exists():
        fail("docs/prediction.json does not exist")

    html = HEALTHCHECK_PATH.read_text(encoding="utf-8")

    required_healthcheck_tokens = [
        "STEP96_RECOMMENDATION_REASON_HEALTHCHECK_STYLE",
        "STEP96_RECOMMENDATION_REASON_HEALTHCHECK_HTML",
        "STEP96_RECOMMENDATION_REASON_HEALTHCHECK_SCRIPT",
        "step96RecommendationReasonHealthPanel",
        "step96RecommendationReasonHealthStatus",
        "step96LoadRecommendationReasonHealth",
        "recommendation_reasoning",
        "recommendation_reason",
        "reason_points",
        "value_grade",
        "risk_note",
        "推奨理由 Health Check",
    ]

    missing_tokens = [token for token in required_healthcheck_tokens if token not in html]
    if missing_tokens:
        fail(f"Missing STEP96 healthcheck tokens: {missing_tokens}")

    print("Healthcheck STEP96 recommendation reason summary markers: OK")

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
    alerts = data.get("alerts", [])

    if not isinstance(races, list) or not races:
        fail("races must be a non-empty list")

    if not isinstance(alerts, list):
        fail("alerts must be a list")

    total = 0
    with_reason = 0
    with_points = 0
    with_grade = 0
    with_risk_note = 0
    with_reason_version = 0
    high_ev_reason = 0
    grade_counts = {}

    errors = []

    for race_index, race in enumerate(races):
        race_no = race.get("race_no") or race.get("race_number") or f"index-{race_index}"
        recommendations = race.get("recommendations", [])

        if not isinstance(recommendations, list):
            fail(f"race {race_no} recommendations must be a list")

        for rec_index, rec in enumerate(recommendations):
            if not isinstance(rec, dict):
                fail(f"race {race_no} recommendation {rec_index} must be an object")

            total += 1

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

            if isinstance(reason, str) and reason.strip():
                with_reason += 1
            else:
                errors.append(f"{label}: missing recommendation_reason")

            if isinstance(points, list) and len(points) >= 2:
                if all(isinstance(p, str) and p.strip() for p in points):
                    with_points += 1
                else:
                    errors.append(f"{label}: reason_points contains empty/non-string item")
            else:
                errors.append(f"{label}: missing reason_points or too few points")

            if isinstance(grade, str) and grade.strip():
                with_grade += 1
                grade_counts[grade] = grade_counts.get(grade, 0) + 1
            else:
                errors.append(f"{label}: missing value_grade")

            if isinstance(risk_note, str) and risk_note.strip():
                with_risk_note += 1
            else:
                errors.append(f"{label}: missing risk_note")

            if reason_version == EXPECTED_REASON_VERSION:
                with_reason_version += 1
            else:
                errors.append(f"{label}: invalid reason_version={reason_version}")

            if ev >= HIGH_EV_THRESHOLD and isinstance(reason, str) and reason.strip():
                high_ev_reason += 1

    if total == 0:
        fail("No recommendations found")

    expected_total = reasoning.get("total_recommendations")
    enriched_total = reasoning.get("enriched_recommendations")

    if expected_total is not None and int(expected_total) != total:
        errors.append(
            f"recommendation_reasoning.total_recommendations mismatch: "
            f"{expected_total} != {total}"
        )

    if enriched_total is not None and int(enriched_total) != total:
        errors.append(
            f"recommendation_reasoning.enriched_recommendations mismatch: "
            f"{enriched_total} != {total}"
        )

    if high_ev_reason < 1:
        errors.append(f"No high-EV recommendation reason found, threshold={HIGH_EV_THRESHOLD}")

    print("recommendation_reasoning:", reasoning)
    print("races:", len(races))
    print("alerts:", len(alerts))
    print("total_recommendations:", total)
    print("with_reason:", with_reason)
    print("with_points:", with_points)
    print("with_grade:", with_grade)
    print("with_risk_note:", with_risk_note)
    print("with_reason_version:", with_reason_version)
    print("high_ev_reason:", high_ev_reason)
    print("grade_counts:", grade_counts)

    if errors:
        print("Validation errors:")
        for e in errors[:100]:
            print("-", e)
        fail(f"{len(errors)} validation errors found")

    print("Healthcheck recommendation reason summary validation: OK")
    print("STEP 97 CHECK: OK")


if __name__ == "__main__":
    main()
