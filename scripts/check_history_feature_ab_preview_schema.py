#!/usr/bin/env python3
import json
from pathlib import Path

SCHEMA_PATH = Path("docs/history-feature-ab-preview-schema.json")
CONFIG_PATH = Path("data/history_feature_config.json")

def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"invalid JSON: {path}: {exc}")

def main():
    errors = []

    if not SCHEMA_PATH.exists():
        errors.append(f"missing file: {SCHEMA_PATH}")
    if not CONFIG_PATH.exists():
        errors.append(f"missing file: {CONFIG_PATH}")

    if errors:
        print("History feature A/B preview schema validation: FAILED")
        for e in errors:
            print("ERROR: " + e)
        raise SystemExit(1)

    schema = load_json(SCHEMA_PATH)
    config = load_json(CONFIG_PATH)

    required = [
        "version",
        "description",
        "target_file",
        "safety",
        "required_top_level_keys",
        "summary_keys",
        "comparison_item_keys",
        "history_feature_snapshot_keys",
        "dry_run_adjustment_candidate_keys",
        "required_safety_values",
        "planned_next_file"
    ]

    for key in required:
        if key not in schema:
            errors.append(f"schema missing key: {key}")

    if schema.get("target_file") != "docs/prediction_history_feature_ab_preview.json":
        errors.append("target_file must be docs/prediction_history_feature_ab_preview.json")

    safety = schema.get("safety", {})
    if safety.get("enabled_required") is not False:
        errors.append("safety.enabled_required must be false")
    if safety.get("affects_prediction_output") is not False:
        errors.append("safety.affects_prediction_output must be false")
    if safety.get("prediction_output_modified") is not False:
        errors.append("safety.prediction_output_modified must be false")

    required_safety_values = schema.get("required_safety_values", {})
    for key in ["history_features_enabled", "affects_prediction_output", "prediction_output_modified", "applied_to_prediction"]:
        if required_safety_values.get(key) is not False:
            errors.append(f"required_safety_values.{key} must be false")

    if config.get("enabled") is not False:
        errors.append("data/history_feature_config.json enabled must remain false")

    for list_key in ["required_top_level_keys", "summary_keys", "comparison_item_keys"]:
        if not isinstance(schema.get(list_key), list) or not schema.get(list_key):
            errors.append(f"{list_key} must be a non-empty list")

    needed_top = [
        "history_features_enabled",
        "affects_prediction_output",
        "prediction_output_modified",
        "summary",
        "comparison_items"
    ]
    top_keys = schema.get("required_top_level_keys", [])
    for key in needed_top:
        if key not in top_keys:
            errors.append(f"required_top_level_keys missing {key}")

    if errors:
        print("History feature A/B preview schema validation: FAILED")
        for e in errors:
            print("ERROR: " + e)
        raise SystemExit(1)

    print("schema file:", SCHEMA_PATH)
    print("target file:", schema.get("target_file"))
    print("planned next file:", schema.get("planned_next_file"))
    print("History feature A/B preview schema validation: OK")
    print("STEP 135-B CHECK: OK")

if __name__ == "__main__":
    main()
