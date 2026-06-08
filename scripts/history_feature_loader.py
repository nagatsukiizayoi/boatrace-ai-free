#!/usr/bin/env python3
import csv
import json
from pathlib import Path

CONFIG_PATH = Path("data/history_feature_config.json")

NUMERIC_FIELDS = {
    "race_count",
    "win_count",
    "top2_count",
    "top3_count",
    "win_rate",
    "top2_rate",
    "top3_rate",
    "avg_start_timing",
}

def _to_number(value):
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    try:
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        try:
            return float(text)
        except ValueError:
            return value

def load_history_feature_config(path=CONFIG_PATH):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"missing config: {path}")
    return json.loads(path.read_text(encoding="utf-8"))

def history_features_enabled(config):
    return bool(config.get("enabled", False))

def get_racer_feature_source_path(config):
    src = config.get("feature_sources", {}).get("racer_history_features", {})
    path = src.get("path")
    if not path:
        raise ValueError("racer_history_features.path is missing in config")
    return Path(path)

def get_default_feature_values(config):
    policy = config.get("prediction_join_policy", {})
    defaults = policy.get("default_values", {})
    return dict(defaults)

def normalize_racer_id(value):
    if value is None:
        return ""
    return str(value).strip()

def normalize_feature_row(row):
    result = {}
    for key, value in row.items():
        if key in NUMERIC_FIELDS:
            result[key] = _to_number(value)
        else:
            result[key] = "" if value is None else str(value).strip()
    return result

def load_racer_history_features(config=None, csv_path=None):
    if config is None:
        config = load_history_feature_config()
    if csv_path is None:
        csv_path = get_racer_feature_source_path(config)

    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"missing racer history feature CSV: {csv_path}")

    features = {}
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {csv_path}")
        if "racer_id" not in reader.fieldnames:
            raise ValueError(f"CSV missing racer_id column: {csv_path}")

        for row in reader:
            racer_id = normalize_racer_id(row.get("racer_id"))
            if not racer_id:
                continue
            normalized = normalize_feature_row(row)
            normalized["history_feature_available"] = True
            features[racer_id] = normalized

    return features

def get_racer_history_feature(racer_id, feature_map, config=None):
    rid = normalize_racer_id(racer_id)
    if rid and rid in feature_map:
        return dict(feature_map[rid])

    if config is None:
        config = load_history_feature_config()

    defaults = get_default_feature_values(config)
    result = dict(defaults)
    result["racer_id"] = rid
    result["history_feature_available"] = False
    return result

def main():
    config = load_history_feature_config()
    enabled = history_features_enabled(config)
    csv_path = get_racer_feature_source_path(config)
    defaults = get_default_feature_values(config)
    features = load_racer_history_features(config, csv_path)

    print("history feature config:", CONFIG_PATH)
    print("history features enabled:", enabled)
    print("racer history feature CSV:", csv_path)
    print("loaded racer feature count:", len(features))
    print("default feature keys:", sorted(defaults.keys()))

    if not features:
        print("ERROR: no racer history features loaded")
        raise SystemExit(1)

    sample_id = sorted(features.keys())[0]
    sample = get_racer_history_feature(sample_id, features, config)
    missing = get_racer_history_feature("__missing_racer_id__", features, config)

    print("sample racer_id:", sample_id)
    print("sample history_feature_available:", sample.get("history_feature_available"))
    print("missing history_feature_available:", missing.get("history_feature_available"))

    if sample.get("history_feature_available") is not True:
        print("ERROR: sample feature was not marked available")
        raise SystemExit(1)

    if missing.get("history_feature_available") is not False:
        print("ERROR: missing feature was not marked unavailable")
        raise SystemExit(1)

    print("History feature loader dry-run: OK")
    print("STEP 134-B CHECK: OK")

if __name__ == "__main__":
    main()
