#!/usr/bin/env python3
import json
from pathlib import Path

INDEX_PATH = Path("docs/index.html")
AB_PREVIEW_PATH = Path("docs/prediction_history_feature_ab_preview.json")
CHECK_SCRIPT_PATH = Path("scripts/check_history_feature_ab_preview.py")

def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"invalid JSON: {path}: {exc}")

def main():
    errors = []

    for path in [INDEX_PATH, AB_PREVIEW_PATH, CHECK_SCRIPT_PATH]:
        if not path.exists():
            errors.append(f"missing file: {path}")

    if errors:
        print("Dashboard history feature A/B preview validation: FAILED")
        for e in errors:
            print("ERROR: " + e)
        raise SystemExit(1)

    html = INDEX_PATH.read_text(encoding="utf-8")
    required_fragments = [
        "history-feature-ab-preview-section",
        "prediction_history_feature_ab_preview.json",
        "履歴特徴量 A/B 比較 preview",
        "enabled:false",
        "hfab-enabled",
        "hfab-affects",
        "hfab-modified",
        "hfab-item-count",
        "hfab-matched-count",
        "hfab-missing-count",
        "hfab-rank-change-count",
        "hfab-recommendation-change-count",
    ]

    for fragment in required_fragments:
        if fragment not in html:
            errors.append(f"docs/index.html missing fragment: {fragment}")

    data = load_json(AB_PREVIEW_PATH)

    if data.get("history_features_enabled") is not False:
        errors.append("history_features_enabled must be false")
    if data.get("affects_prediction_output") is not False:
        errors.append("affects_prediction_output must be false")
    if data.get("prediction_output_modified") is not False:
        errors.append("prediction_output_modified must be false")

    summary = data.get("summary")
    if not isinstance(summary, dict):
        errors.append("summary must be an object")
    else:
        for key in [
            "comparison_item_count",
            "history_feature_matched_count",
            "history_feature_missing_count",
            "rank_change_candidate_count",
            "recommendation_change_candidate_count",
        ]:
            if key not in summary:
                errors.append(f"summary missing key: {key}")

    if errors:
        print("Dashboard history feature A/B preview validation: FAILED")
        for e in errors:
            print("ERROR: " + e)
        raise SystemExit(1)

    print("Dashboard history feature A/B preview validation: OK")
    print("STEP 135-G CHECK: OK")

if __name__ == "__main__":
    main()
