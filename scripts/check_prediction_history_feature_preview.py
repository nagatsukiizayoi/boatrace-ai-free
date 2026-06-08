#!/usr/bin/env python3
import json
from pathlib import Path

PREVIEW_PATH = Path("docs/prediction_history_feature_preview.json")
EXPORT_SCRIPT_PATH = Path("scripts/export_prediction_history_feature_preview.py")
CONFIG_PATH = Path("data/history_feature_config.json")

def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"invalid JSON: {path}: {exc}")

def main():
    errors = []
    warnings = []

    if not PREVIEW_PATH.exists():
        errors.append(f"missing file: {PREVIEW_PATH}")

    if not EXPORT_SCRIPT_PATH.exists():
        errors.append(f"missing file: {EXPORT_SCRIPT_PATH}")

    if not CONFIG_PATH.exists():
        errors.append(f"missing file: {CONFIG_PATH}")

    if errors:
        print("Prediction history feature preview validation: FAILED")
        for e in errors:
            print("ERROR: " + e)
        raise SystemExit(1)

    preview = load_json(PREVIEW_PATH)
    config = load_json(CONFIG_PATH)

    required_keys = [
        "version",
        "description",
        "source_prediction",
        "history_features_enabled",
        "affects_prediction_output",
        "prediction_output_modified",
        "racer_id_count",
        "matched_racer_id_count",
        "missing_racer_id_count",
        "loaded_feature_racer_count",
        "entries",
        "notes",
    ]

    for key in required_keys:
        if key not in preview:
            errors.append(f"preview missing key: {key}")

    if preview.get("history_features_enabled") is not False:
        errors.append("history_features_enabled must be false in preview stage")

    if preview.get("affects_prediction_output") is not False:
        errors.append("affects_prediction_output must be false")

    if preview.get("prediction_output_modified") is not False:
        errors.append("prediction_output_modified must be false")

    if config.get("enabled") is not False:
        errors.append("data/history_feature_config.json enabled must remain false")

    for key in ["racer_id_count", "matched_racer_id_count", "missing_racer_id_count", "loaded_feature_racer_count"]:
        value = preview.get(key)
        if not isinstance(value, int):
            errors.append(f"{key} must be an integer")
        elif value < 0:
            errors.append(f"{key} must be non-negative")

    entries = preview.get("entries")
    if not isinstance(entries, list):
        errors.append("entries must be a list")
    else:
        if len(entries) != int(preview.get("racer_id_count", 0) or 0):
            warnings.append("entries length does not match racer_id_count")
        for i, entry in enumerate(entries[:20]):
            if not isinstance(entry, dict):
                errors.append(f"entry {i} must be an object")
                continue
            if "racer_id" not in entry:
                errors.append(f"entry {i} missing racer_id")
            if "history_feature_available" not in entry:
                errors.append(f"entry {i} missing history_feature_available")
            if "features" not in entry:
                errors.append(f"entry {i} missing features")
            elif not isinstance(entry.get("features"), dict):
                errors.append(f"entry {i} features must be an object")

    notes = preview.get("notes", [])
    joined_notes = " ".join(str(x) for x in notes) if isinstance(notes, list) else str(notes)
    if "enabled:false" not in joined_notes:
        warnings.append("notes do not mention enabled:false")
    if "not modified" not in joined_notes and "変更" not in joined_notes:
        warnings.append("notes may not clearly state prediction JSON is not modified")

    print("preview file:", PREVIEW_PATH)
    print("history features enabled:", preview.get("history_features_enabled"))
    print("affects prediction output:", preview.get("affects_prediction_output"))
    print("prediction output modified:", preview.get("prediction_output_modified"))
    print("racer id count:", preview.get("racer_id_count"))
    print("matched racer id count:", preview.get("matched_racer_id_count"))
    print("missing racer id count:", preview.get("missing_racer_id_count"))
    print("loaded feature racer count:", preview.get("loaded_feature_racer_count"))

    for w in warnings:
        print("WARNING:", w)

    if errors:
        print("Prediction history feature preview validation: FAILED")
        for e in errors:
            print("ERROR: " + e)
        raise SystemExit(1)

    print("Prediction history feature preview validation: OK")
    print("STEP 134-G CHECK: OK")

if __name__ == "__main__":
    main()
