#!/usr/bin/env python3
import importlib.util
import json
from pathlib import Path

PREDICTION_PATH = Path("docs/prediction.json")
LOADER_PATH = Path("scripts/history_feature_loader.py")
OUTPUT_PATH = Path("docs/prediction_history_feature_preview.json")

RACER_ID_KEYS = {
    "racer_id",
    "player_id",
    "racerId",
    "playerId",
    "registration_number",
    "toban",
}

FEATURE_KEYS = [
    "race_count",
    "win_rate",
    "top2_rate",
    "top3_rate",
    "avg_start_timing",
    "last_race_date",
]

def import_loader():
    spec = importlib.util.spec_from_file_location("history_feature_loader", LOADER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load history_feature_loader module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def collect_racer_ids(obj, found):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in RACER_ID_KEYS:
                text = "" if value is None else str(value).strip()
                if text:
                    found.add(text)
            collect_racer_ids(value, found)
    elif isinstance(obj, list):
        for item in obj:
            collect_racer_ids(item, found)

def slim_feature(feature):
    result = {}
    for key in FEATURE_KEYS:
        result[key] = feature.get(key)
    result["history_feature_available"] = bool(feature.get("history_feature_available"))
    return result

def main():
    if not PREDICTION_PATH.exists():
        print(f"ERROR: missing file: {PREDICTION_PATH}")
        raise SystemExit(1)

    prediction = json.loads(PREDICTION_PATH.read_text(encoding="utf-8"))

    loader = import_loader()
    config = loader.load_history_feature_config()
    enabled = loader.history_features_enabled(config)
    feature_map = loader.load_racer_history_features(config)

    racer_ids = set()
    collect_racer_ids(prediction, racer_ids)

    entries = []
    matched = 0
    missing = 0

    for rid in sorted(racer_ids):
        feature = loader.get_racer_history_feature(rid, feature_map, config)
        available = feature.get("history_feature_available") is True
        if available:
            matched += 1
        else:
            missing += 1
        entries.append({
            "racer_id": rid,
            "history_feature_available": available,
            "features": slim_feature(feature),
        })

    preview = {
        "version": "1.0",
        "description": "Dry-run preview of joining prediction JSON racer IDs with history features. This file does not affect prediction output.",
        "source_prediction": str(PREDICTION_PATH),
        "history_features_enabled": enabled,
        "affects_prediction_output": False,
        "prediction_output_modified": False,
        "racer_id_count": len(racer_ids),
        "matched_racer_id_count": matched,
        "missing_racer_id_count": missing,
        "loaded_feature_racer_count": len(feature_map),
        "entries": entries,
        "notes": [
            "data/history_feature_config.json remains enabled:false.",
            "This preview is for validation only.",
            "docs/prediction.json is not modified by this script."
        ],
    }

    OUTPUT_PATH.write_text(json.dumps(preview, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("saved preview:", OUTPUT_PATH)
    print("history features enabled:", enabled)
    print("prediction racer ids:", len(racer_ids))
    print("matched racer ids:", matched)
    print("missing racer ids:", missing)

    if enabled is not False:
        print("ERROR: history features should remain disabled for preview stage")
        raise SystemExit(1)

    print("Prediction history feature preview export: OK")
    print("STEP 134-F CHECK: OK")

if __name__ == "__main__":
    main()
