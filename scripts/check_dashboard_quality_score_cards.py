#!/usr/bin/env python3
import json
import sys
from pathlib import Path


INDEX_PATH = Path("docs/index.html")
PREDICTION_JSON_PATH = Path("docs/prediction.json")

HIGH_EV_THRESHOLD = 1.2
MIN_QUALITY_SCORE = 75


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def to_float(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def has_text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def expected_value_alert(alert: dict) -> bool:
    text = json.dumps(alert or {}, ensure_ascii=False)
    return "期待値" in text or "expected_value" in text or "EV" in text


def ratio_score(count: int, total: int, weight: int) -> int:
    if total <= 0:
        return 0
    return round((count / total) * weight)


def score_grade(score: int) -> str:
    if score >= 90:
        return "EXCELLENT"
    if score >= 75:
        return "GOOD"
    if score >= 60:
        return "WARN"
    return "BAD"


def main() -> None:
    if not INDEX_PATH.exists():
        fail("docs/index.html does not exist")

    if not PREDICTION_JSON_PATH.exists():
        fail("docs/prediction.json does not exist")

    html = INDEX_PATH.read_text(encoding="utf-8")

    required_index_tokens = [
        "STEP98_QUALITY_SCORE_CARDS_STYLE",
        "STEP98_QUALITY_SCORE_CARDS_HTML",
        "STEP98_QUALITY_SCORE_CARDS_SCRIPT",
        "step98QualityScorePanel",
        "step98QualityStatus",
        "step98QualityScore",
        "step98QualityGrade",
        "step98TotalRecommendations",
        "step98OddsCount",
        "step98EvCount",
        "step98HighEvCount",
        "step98ReasonCount",
        "step98ReasonPointsCount",
        "step98ExpectedValueAlerts",
        "step98RaceCount",
        "step98LoadQualityScore",
        "予想データ品質スコア",
        "expected_value",
        "odds",
        "recommendation_reason",
    ]

    missing_index_tokens = [token for token in required_index_tokens if token not in html]
    if missing_index_tokens:
        fail(f"Missing STEP98 quality score card tokens: {missing_index_tokens}")

    print("Dashboard STEP98 quality score card markers: OK")

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

    races = data.get("races", [])
    alerts = data.get("alerts", [])
    reasoning = data.get("recommendation_reasoning", {})

    if not isinstance(races, list) or not races:
        fail("races must be a non-empty list")

    if not isinstance(alerts, list):
        fail("alerts must be a list")

    if not isinstance(reasoning, dict):
        fail("recommendation_reasoning must be an object")

    recommendations = []

    for race_index, race in enumerate(races):
        race_no = race.get("race_no") or race.get("race_number") or f"index-{race_index}"
        recs = race.get("recommendations", [])

        if not isinstance(recs, list):
            fail(f"race {race_no} recommendations must be a list")

        for rec_index, rec in enumerate(recs):
            if not isinstance(rec, dict):
                fail(f"race {race_no} recommendation {rec_index} must be an object")

            recommendations.append(
                {
                    "race_no": race_no,
                    "rec_index": rec_index,
                    "bet_type": rec.get("bet_type"),
                    "combination": rec.get("combination"),
                    "odds": to_float(rec.get("odds")),
                    "expected_value": to_float(rec.get("expected_value")),
                    "recommendation_reason": rec.get("recommendation_reason"),
                    "reason_points": rec.get("reason_points"),
                    "risk_note": rec.get("risk_note"),
                    "value_grade": rec.get("value_grade"),
                }
            )

    total = len(recommendations)
    if total == 0:
        fail("No recommendations found")

    odds_count = sum(1 for r in recommendations if r["odds"] > 0)
    ev_count = sum(1 for r in recommendations if r["expected_value"] > 0)
    high_ev_count = sum(1 for r in recommendations if r["expected_value"] >= HIGH_EV_THRESHOLD)
    reason_count = sum(1 for r in recommendations if has_text(r["recommendation_reason"]))
    points_count = sum(
        1
        for r in recommendations
        if isinstance(r["reason_points"], list) and len(r["reason_points"]) >= 2
    )
    risk_count = sum(1 for r in recommendations if has_text(r["risk_note"]))
    expected_value_alert_count = sum(1 for a in alerts if expected_value_alert(a))

    score = 0
    score += 10 if len(races) > 0 else 0
    score += 10 if total > 0 else 0
    score += ratio_score(odds_count, total, 15)
    score += ratio_score(ev_count, total, 15)
    score += 10 if high_ev_count > 0 else 0
    score += 10 if expected_value_alert_count > 0 else 0
    score += ratio_score(reason_count, total, 15)
    score += ratio_score(points_count, total, 10)
    score += ratio_score(risk_count, total, 5)
    score += 10 if reasoning.get("enabled") is True else 0

    score = min(score, 100)
    grade = score_grade(score)

    print("races:", len(races))
    print("alerts:", len(alerts))
    print("recommendations:", total)
    print("odds_count:", odds_count)
    print("ev_count:", ev_count)
    print("high_ev_count:", high_ev_count)
    print("reason_count:", reason_count)
    print("points_count:", points_count)
    print("risk_count:", risk_count)
    print("expected_value_alert_count:", expected_value_alert_count)
    print("recommendation_reasoning.enabled:", reasoning.get("enabled"))
    print("quality_score:", score)
    print("quality_grade:", grade)

    errors = []

    if odds_count < 1:
        errors.append("No recommendation with odds > 0")

    if ev_count < 1:
        errors.append("No recommendation with expected_value > 0")

    if high_ev_count < 1:
        errors.append(f"No high EV recommendation expected_value >= {HIGH_EV_THRESHOLD}")

    if expected_value_alert_count < 1:
        errors.append("No expected value alert found")

    if reason_count != total:
        errors.append(f"Not all recommendations have recommendation_reason: {reason_count}/{total}")

    if points_count != total:
        errors.append(f"Not all recommendations have enough reason_points: {points_count}/{total}")

    if risk_count != total:
        errors.append(f"Not all recommendations have risk_note: {risk_count}/{total}")

    if reasoning.get("enabled") is not True:
        errors.append("recommendation_reasoning.enabled must be true")

    if score < MIN_QUALITY_SCORE:
        errors.append(f"quality_score must be >= {MIN_QUALITY_SCORE}, got {score}")

    print("High EV preview:")
    high_ev_items = sorted(
        [r for r in recommendations if r["expected_value"] >= HIGH_EV_THRESHOLD],
        key=lambda r: r["expected_value"],
        reverse=True,
    )

    for item in high_ev_items[:10]:
        print(
            f'{item["race_no"]}R',
            item["bet_type"],
            item["combination"],
            "odds=", item["odds"],
            "EV=", item["expected_value"],
            "grade=", item["value_grade"],
        )

    if errors:
        print("Validation errors:")
        for e in errors:
            print("-", e)
        fail(f"{len(errors)} quality score validation errors found")

    print("Dashboard quality score card validation: OK")
    print("STEP 99 CHECK: OK")


if __name__ == "__main__":
    main()
