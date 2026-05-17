#!/usr/bin/env python3
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


PREDICTION_JSON_PATH = Path("docs/prediction.json")
REASON_VERSION = "recommendation_reason_v1"
HIGH_EV_THRESHOLD = 1.2


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def to_float(value, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def to_int(value, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def value_grade(expected_value: float) -> str:
    if expected_value >= 5.0:
        return "S"
    if expected_value >= 2.0:
        return "A"
    if expected_value >= 1.2:
        return "B"
    if expected_value > 0:
        return "C"
    return "UNKNOWN"


def risk_note(odds: float, expected_value: float, probability: float) -> str:
    if odds >= 20:
        return "超高オッズのため的中率は低めに見積もり、資金配分は控えめにしてください"
    if odds >= 10:
        return "高オッズのためブレが大きく、連敗リスクに注意してください"
    if expected_value >= 2.0:
        return "期待値は高めですが、過信せず少額分散を推奨します"
    if probability > 0 and probability < 0.15:
        return "推定的中確率が低めのため、資金管理を重視してください"
    if expected_value >= HIGH_EV_THRESHOLD:
        return "期待値基準は満たしていますが、オッズ変動に注意してください"
    return "期待値基準未満のため、参考候補として扱ってください"


def build_reason_points(rec: dict) -> list[str]:
    bet_type = rec.get("bet_type") or "-"
    combination = rec.get("combination") or "-"
    odds = to_float(rec.get("odds"))
    ev = to_float(rec.get("expected_value"))
    amount = to_int(rec.get("amount"))
    probability = to_float(rec.get("probability"))
    confidence = to_float(rec.get("confidence"))

    points = []

    points.append(f"買い目は {bet_type} {combination} です")

    if ev >= HIGH_EV_THRESHOLD:
        points.append(f"expected_value={ev:.2f} が基準値 {HIGH_EV_THRESHOLD:.2f} を上回っています")
    elif ev > 0:
        points.append(f"expected_value={ev:.2f} は基準値 {HIGH_EV_THRESHOLD:.2f} 未満です")
    else:
        points.append("expected_value が未設定または 0 のため、期待値評価は参考扱いです")

    if odds >= 10:
        points.append(f"odds={odds:.2f} の高配当候補です")
    elif odds > 0:
        points.append(f"odds={odds:.2f} のオッズが反映されています")
    else:
        points.append("odds が未設定のため、オッズ評価は未反映です")

    if probability > 0:
        points.append(f"推定確率 probability={probability:.3f} を使用しています")

    if confidence > 0:
        points.append(f"信頼度 confidence={confidence:.3f} を使用しています")

    if amount > 0:
        points.append(f"購入金額 amount={amount} 円で資金配分されています")

    return points


def build_recommendation_reason(rec: dict) -> str:
    bet_type = rec.get("bet_type") or "-"
    combination = rec.get("combination") or "-"
    odds = to_float(rec.get("odds"))
    ev = to_float(rec.get("expected_value"))
    probability = to_float(rec.get("probability"))
    grade = value_grade(ev)

    parts = []

    if ev >= HIGH_EV_THRESHOLD:
        parts.append(f"EV {ev:.2f} の高期待値買い目です")
    elif ev > 0:
        parts.append(f"EV {ev:.2f} の参考買い目です")
    else:
        parts.append("EV 未反映の参考買い目です")

    if odds > 0:
        parts.append(f"オッズ {odds:.2f} 倍を反映しています")

    if probability > 0:
        parts.append(f"推定確率 {probability:.3f} を考慮しています")

    parts.append(f"評価グレードは {grade} です")

    return "。".join(parts) + f"。対象買い目は {bet_type} {combination} です。"


def enrich_recommendation(rec: dict) -> dict:
    odds = to_float(rec.get("odds"))
    ev = to_float(rec.get("expected_value"))
    probability = to_float(rec.get("probability"))

    rec["recommendation_reason"] = build_recommendation_reason(rec)
    rec["reason_points"] = build_reason_points(rec)
    rec["value_grade"] = value_grade(ev)
    rec["risk_note"] = risk_note(odds, ev, probability)
    rec["reason_version"] = REASON_VERSION

    return rec


def main() -> None:
    if not PREDICTION_JSON_PATH.exists():
        fail("docs/prediction.json does not exist")

    try:
        data = json.loads(PREDICTION_JSON_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        fail(f"Invalid JSON: {e}")

    races = data.get("races", [])
    if not isinstance(races, list) or not races:
        fail("prediction.json races must be a non-empty list")

    total_recommendations = 0
    enriched_count = 0
    high_ev_count = 0
    grade_counts = {}

    for race in races:
        recs = race.get("recommendations", [])

        if not isinstance(recs, list):
            continue

        for rec in recs:
            if not isinstance(rec, dict):
                continue

            total_recommendations += 1
            enrich_recommendation(rec)
            enriched_count += 1

            ev = to_float(rec.get("expected_value"))
            if ev >= HIGH_EV_THRESHOLD:
                high_ev_count += 1

            grade = rec.get("value_grade") or "UNKNOWN"
            grade_counts[grade] = grade_counts.get(grade, 0) + 1

    if total_recommendations == 0:
        fail("No recommendations found")

    if enriched_count == 0:
        fail("No recommendations enriched")

    data["recommendation_reasoning"] = {
        "enabled": True,
        "version": REASON_VERSION,
        "high_ev_threshold": HIGH_EV_THRESHOLD,
        "total_recommendations": total_recommendations,
        "enriched_recommendations": enriched_count,
        "high_ev_recommendations": high_ev_count,
        "grade_counts": grade_counts,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    PREDICTION_JSON_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("Recommendation reasons enriched")
    print("total_recommendations:", total_recommendations)
    print("enriched_recommendations:", enriched_count)
    print("high_ev_recommendations:", high_ev_count)
    print("grade_counts:", grade_counts)
    print("STEP 90 CHECK: OK")


if __name__ == "__main__":
    main()
