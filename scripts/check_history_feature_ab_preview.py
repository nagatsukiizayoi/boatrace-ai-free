#!/usr/bin/env python3
import json
from pathlib import Path

AB_PREVIEW_PATH = Path("docs/prediction_history_feature_ab_preview.json")
SCHEMA_PATH = Path("docs/history-feature-ab-preview-schema.json")
EXPORT_SCRIPT_PATH = Path("scripts/export_history_feature_ab_preview.py")
CONFIG_PATH = Path("data/history_feature_config.json")

def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"invalid JSON: {path}: {exc}")

def main():
    errors = []
    warnings = []

    required_files = [
        AB_PREVIEW_PATH,
        SCHEMA_PATH,
        EXPORT_SCRIPT_PATH,
        CONFIG_PATH,
    ]

    for path in required_files:
        if not path.exists():
            errors.append(f"missing file: {path}")

    if errors:
        print("History feature A/B preview validation: FAILED")
        for e in errors:
            print("ERROR: " + e)
        raise SystemExit(1)

    preview = load_json(AB_PREVIEW_PATH)
    schema = load_json(SCHEMA_PATH)
    config = load_json(CONFIG_PATH)

    required_top = schema.get("required_top_level_keys", [])
    for key in required_top:
        if key not in preview:
            errors.append(f"A/B preview missing top-level key: {key}")

    if preview.get("history_features_enabled") is not False:
        errors.append("history_features_enabled must be false")

    if preview.get("affects_prediction_output") is not False:
        errors.append("affects_prediction_output must be false")

    if preview.get("prediction_output_modified") is not False:
        errors.append("prediction_output_modified must be false")

    if config.get("enabled") is not False:
        errors.append("data/history_feature_config.json enabled must remain false")

    summary = preview.get("summary")
    if not isinstance(summary, dict):
        errors.append("summary must be an object")
        summary = {}

    for key in schema.get("summary_keys", []):
        if key not in summary:
            errors.append(f"summary missing key: {key}")

    for key in [
        "prediction_racer_id_count",
        "history_feature_matched_count",
        "history_feature_missing_count",
        "comparison_item_count",
        "rank_change_candidate_count",
        "recommendation_change_candidate_count",
    ]:
        value = summary.get(key)
        if value is not None and not isinstance(value, int):
            errors.append(f"summary.{key} must be an integer")

    comparison_items = preview.get("comparison_items")
    if not isinstance(comparison_items, list):
        errors.append("comparison_items must be a list")
        comparison_items = []

    expected_count = summary.get("comparison_item_count")
    if isinstance(expected_count, int) and expected_count != len(comparison_items):
        warnings.append("summary.comparison_item_count does not match comparison_items length")

    item_required = schema.get("comparison_item_keys", [])
    candidate_required = schema.get("dry_run_adjustment_candidate_keys", [])

    for i, item in enumerate(comparison_items[:50]):
        if not isinstance(item, dict):
            errors.append(f"comparison_items[{i}] must be an object")
            continue

        for key in item_required:
            if key not in item:
                errors.append(f"comparison_items[{i}] missing key: {key}")

        candidate = item.get("dry_run_adjustment_candidate")
        if not isinstance(candidate, dict):
            errors.append(f"comparison_items[{i}].dry_run_adjustment_candidate must be an object")
            continue

        for key in candidate_required:
            if key not in candidate:
                errors.append(f"comparison_items[{i}].dry_run_adjustment_candidate missing key: {key}")

        if candidate.get("applied_to_prediction") is not False:
            errors.append(f"comparison_items[{i}].applied_to_prediction must be false")

    notes = preview.get("notes", [])
    notes_text = " ".join(str(x) for x in notes) if isinstance(notes, list) else str(notes)
    if "enabled:false" not in notes_text:
        warnings.append("notes do not mention enabled:false")
    if "not modified" not in notes_text and "No adjustment" not in notes_text:
        warnings.append("notes may not clearly state prediction output is not modified")

    print("A/B preview file:", AB_PREVIEW_PATH)
    print("history features enabled:", preview.get("history_features_enabled"))
    print("affects prediction output:", preview.get("affects_prediction_output"))
    print("prediction output modified:", preview.get("prediction_output_modified"))
    print("comparison item count:", len(comparison_items))
    print("rank change candidate count:", summary.get("rank_change_candidate_count"))
    print("recommendation change candidate count:", summary.get("recommendation_change_candidate_count"))

    for w in warnings:
        print("WARNING:", w)

    if errors:
        print("History feature A/B preview validation: FAILED")
        for e in errors:
            print("ERROR: " + e)
        raise SystemExit(1)

    print("History feature A/B preview validation: OK")
    print("STEP 135-E CHECK: OK")

if __name__ == "__main__":
    main()
