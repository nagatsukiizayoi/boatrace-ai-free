#!/usr/bin/env python3
import importlib.util
from pathlib import Path

LOADER_PATH = Path("scripts/history_feature_loader.py")
CONFIG_PATH = Path("data/history_feature_config.json")
FEATURE_CSV_PATH = Path("data/import/history/racer_history_features.csv")

def import_loader():
    spec = importlib.util.spec_from_file_location("history_feature_loader", LOADER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load history_feature_loader module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    errors = []

    for path in [LOADER_PATH, CONFIG_PATH, FEATURE_CSV_PATH]:
        if not path.exists():
            errors.append(f"missing file: {path}")

    if errors:
        print("History feature loader validation: FAILED")
        for e in errors:
            print("ERROR: " + e)
        raise SystemExit(1)

    loader = import_loader()

    try:
        config = loader.load_history_feature_config()
        enabled = loader.history_features_enabled(config)
        csv_path = loader.get_racer_feature_source_path(config)
        defaults = loader.get_default_feature_values(config)
        features = loader.load_racer_history_features(config, csv_path)
    except Exception as exc:
        print("History feature loader validation: FAILED")
        print("ERROR:", exc)
        raise SystemExit(1)

    if enabled is not False:
        errors.append("history_feature_config enabled should remain false at this stage")

    if not defaults:
        errors.append("default feature values are empty")

    required_defaults = ["race_count", "win_rate", "top2_rate", "top3_rate", "avg_start_timing", "last_race_date"]
    for key in required_defaults:
        if key not in defaults:
            errors.append(f"default values missing key: {key}")

    if len(features) <= 0:
        errors.append("no racer features loaded")

    if features:
        sample_id = sorted(features.keys())[0]
        sample = loader.get_racer_history_feature(sample_id, features, config)
        missing = loader.get_racer_history_feature("__missing_racer_id__", features, config)

        if sample.get("history_feature_available") is not True:
            errors.append("existing racer feature should be available")

        if missing.get("history_feature_available") is not False:
            errors.append("missing racer feature should be unavailable")

        for key in ["race_count", "win_rate", "top2_rate", "top3_rate"]:
            if key not in sample:
                errors.append(f"sample feature missing key: {key}")

    if errors:
        print("History feature loader validation: FAILED")
        for e in errors:
            print("ERROR: " + e)
        raise SystemExit(1)

    print("loaded racer feature count:", len(features))
    print("history features enabled:", enabled)
    print("History feature loader validation: OK")
    print("STEP 134-B CHECK: OK")

if __name__ == "__main__":
    main()
