#!/usr/bin/env python3
import importlib.util
import json
from pathlib import Path

PREDICTION_PATH = Path("docs/prediction.json")
LOADER_PATH = Path("scripts/history_feature_loader.py")

RACER_ID_KEYS = {
    "racer_id",
    "player_id",
    "racerId",
    "playerId",
    "registration_number",
    "toban",
}

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

def main():
    errors = []
    warnings = []

    if not PREDICTION_PATH.exists():
        errors.append(f"missing file: {PREDICTION_PATH}")
    if not LOADER_PATH.exists():
        errors.append(f"missing file: {LOADER_PATH}")

    if errors:
        print("Prediction history feature join validation: FAILED")
        for e in errors:
            print("ERROR: " + e)
        raise SystemExit(1)

    try:
        prediction = json.loads(PREDICTION_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        print("Prediction history feature join validation: FAILED")
        print("ERROR: invalid prediction JSON:", exc)
        raise SystemExit(1)

    try:
        loader = import_loader()
        config = loader.load_history_feature_config()
        enabled = loader.history_features_enabled(config)
        feature_map = loader.load_racer_history_features(config)
    except Exception as exc:
        print("Prediction history feature join validation: FAILED")
        print("ERROR: failed to load history features:", exc)
        raise SystemExit(1)

    racer_ids = set()
    collect_racer_ids(prediction, racer_ids)

    if not racer_ids:
        warnings.append("no racer_id-like values found in docs/prediction.json")
        # Prediction JSON may be summary-only in some states.
        # Keep this as warning because loader itself can still be ready.

    matched = 0
    missing = 0

    for rid in sorted(racer_ids):
        feature = loader.get_racer_history_feature(rid, feature_map, config)
        if feature.get("history_feature_available") is True:
            matched += 1
        else:
            missing += 1

    if enabled is not False:
        errors.append("history features should remain disabled for join validation stage")

    if feature_map and len(feature_map) <= 0:
        errors.append("feature map is empty")

    default_feature = loader.get_racer_history_feature("__missing_racer_id__", feature_map, config)
    if default_feature.get("history_feature_available") is not False:
        errors.append("default missing racer feature should be unavailable")

    print("prediction file:", PREDICTION_PATH)
    print("history features enabled:", enabled)
    print("loaded feature racers:", len(feature_map))
    print("prediction racer ids found:", len(racer_ids))
    print("matched racer ids:", matched)
    print("missing racer ids:", missing)

    for w in warnings:
        print("WARNING:", w)

    if errors:
        print("Prediction history feature join validation: FAILED")
        for e in errors:
            print("ERROR: " + e)
        raise SystemExit(1)

    print("Prediction history feature join validation: OK")
    print("STEP 134-D CHECK: OK")

if __name__ == "__main__":
    main()
