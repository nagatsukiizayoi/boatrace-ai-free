#!/usr/bin/env python3
import json
from pathlib import Path

PREDICTION_PATH = Path("docs/prediction.json")
HISTORY_PREVIEW_PATH = Path("docs/prediction_history_feature_preview.json")
SCHEMA_PATH = Path("docs/history-feature-ab-preview-schema.json")
CONFIG_PATH = Path("data/history_feature_config.json")
OUTPUT_PATH = Path("docs/prediction_history_feature_ab_preview.json")

FEATURE_KEYS = [
    "race_count",
    "win_rate",
    "top2_rate",
    "top3_rate",
    "avg_start_timing",
    "last_race_date",
]

def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def to_float(value, default=0.0):
    if value is None or value == "":
        return default
    try:
        return float(value)
    except Exception:
        return default

def to_int(value, default=0):
    if value is None or value == "":
        return default
    try:
        return int(float(value))
    except Exception:
        return default

def make_candidate(feature):
    race_count = to_int(feature.get("race_count"), 0)
    win_rate = to_float(feature.get("win_rate"), 0.0)
    top3_rate = to_float(feature.get("top3_rate"), 0.0)
    avg_st = feature.get("avg_start_timing")

    reasons = []
    score_delta = 0.0

    if race_count <= 0:
        reasons.append("no_history_or_default_values")
    elif race_count < 30:
        reasons.append("low_sample_size")
        score_delta += 0.0
    else:
        reasons.append("sufficient_history_sample")

        if win_rate >= 0.25:
            score_delta += 0.02
            reasons.append("high_win_rate_candidate")
        elif win_rate <= 0.05:
            score_delta -= 0.01
            reasons.append("low_win_rate_candidate")

        if top3_rate >= 0.60:
            score_delta += 0.02
            reasons.append("high_top3_rate_candidate")
        elif top3_rate <= 0.25:
            score_delta -= 0.01
            reasons.append("low_top3_rate_candidate")

        st = to_float(avg_st, None)
        if st is not None:
            if st > 0 and st <= 0.14:
                score_delta += 0.01
                reasons.append("strong_start_timing_candidate")
            elif st >= 0.22:
                score_delta -= 0.005
                reasons.append("slow_start_timing_candidate")

    return {
        "candidate_score_delta": round(score_delta, 4),
        "candidate_reason": reasons,
        "would_change_rank": False,
        "would_change_recommendation": False,
        "applied_to_prediction": False
    }

def main():
    errors = []

    for path in [PREDICTION_PATH, HISTORY_PREVIEW_PATH, SCHEMA_PATH, CONFIG_PATH]:
        if not path.exists():
            errors.append(f"missing file: {path}")

    if errors:
        print("History feature A/B preview export: FAILED")
        for e in errors:
            print("ERROR: " + e)
        raise SystemExit(1)

    prediction = load_json(PREDICTION_PATH)
    history_preview = load_json(HISTORY_PREVIEW_PATH)
    schema = load_json(SCHEMA_PATH)
    config = load_json(CONFIG_PATH)

    if config.get("enabled") is not False:
        print("ERROR: data/history_feature_config.json enabled must remain false")
        raise SystemExit(1)

    if history_preview.get("history_features_enabled") is not False:
        print("ERROR: source history preview must have history_features_enabled:false")
        raise SystemExit(1)

    entries = history_preview.get("entries", [])
    if not isinstance(entries, list):
        print("ERROR: history preview entries must be a list")
        raise SystemExit(1)

    comparison_items = []
    rank_change_candidate_count = 0
    recommendation_change_candidate_count = 0

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        racer_id = str(entry.get("racer_id", "")).strip()
        features = entry.get("features", {})
        if not isinstance(features, dict):
            features = {}

        history_snapshot = {key: features.get(key) for key in FEATURE_KEYS}
        candidate = make_candidate(history_snapshot)

        if candidate.get("would_change_rank"):
            rank_change_candidate_count += 1
        if candidate.get("would_change_recommendation"):
            recommendation_change_candidate_count += 1

        comparison_items.append({
            "racer_id": racer_id,
            "history_feature_available": bool(entry.get("history_feature_available")),
            "current_prediction_snapshot": {
                "source": str(PREDICTION_PATH),
                "rank": None,
                "score": None,
                "probability": None,
                "recommendation_related": None
            },
            "history_feature_snapshot": history_snapshot,
            "dry_run_adjustment_candidate": candidate,
            "notes": [
                "dry-run only",
                "not applied to prediction",
                "enabled:false"
            ]
        })

    matched = int(history_preview.get("matched_racer_id_count", 0) or 0)
    missing = int(history_preview.get("missing_racer_id_count", 0) or 0)
    racer_count = int(history_preview.get("racer_id_count", len(entries)) or 0)

    output = {
        "version": "1.0",
        "description": "Dry-run A/B preview for history feature prediction integration. This file does not modify prediction output.",
        "source_prediction": str(PREDICTION_PATH),
        "source_history_feature_preview": str(HISTORY_PREVIEW_PATH),
        "history_features_enabled": False,
        "affects_prediction_output": False,
        "prediction_output_modified": False,
        "summary": {
            "prediction_racer_id_count": racer_count,
            "history_feature_matched_count": matched,
            "history_feature_missing_count": missing,
            "comparison_item_count": len(comparison_items),
            "rank_change_candidate_count": rank_change_candidate_count,
            "recommendation_change_candidate_count": recommendation_change_candidate_count
        },
        "comparison_items": comparison_items,
        "notes": [
            "This is a dry-run A/B preview.",
            "data/history_feature_config.json remains enabled:false.",
            "Existing prediction JSON files are not modified.",
            "No adjustment is applied to prediction output."
        ],
        "schema": {
            "path": str(SCHEMA_PATH),
            "version": schema.get("version")
        },
        "source_prediction_json_top_level_type": type(prediction).__name__
    }

    OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("saved A/B preview:", OUTPUT_PATH)
    print("history features enabled:", output["history_features_enabled"])
    print("affects prediction output:", output["affects_prediction_output"])
    print("prediction output modified:", output["prediction_output_modified"])
    print("comparison item count:", len(comparison_items))
    print("History feature A/B preview export: OK")
    print("STEP 135-D CHECK: OK")

if __name__ == "__main__":
    main()
