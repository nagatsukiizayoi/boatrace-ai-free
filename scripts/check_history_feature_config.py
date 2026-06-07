#!/usr/bin/env python3
import json
from pathlib import Path

CONFIG_PATH = Path("data/history_feature_config.json")

REQUIRED_TOP_LEVEL_KEYS = [
    "version",
    "description",
    "enabled",
    "feature_sources",
    "prediction_join_policy",
    "feature_usage_plan",
    "safety",
]

REQUIRED_FEATURE_SOURCES = [
    "racer_history_features",
    "racer_history_features_summary",
    "history_database_summary",
]


def main():
    errors = []
    warnings = []

    if not CONFIG_PATH.exists():
        print("History feature config validation: FAILED")
        print(f"ERROR: missing config file: {CONFIG_PATH}")
        raise SystemExit(1)

    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        print("History feature config validation: FAILED")
        print(f"ERROR: invalid JSON: {exc}")
        raise SystemExit(1)

    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in data:
            errors.append(f"missing top-level key: {key}")

    if data.get("enabled") is not False:
        warnings.append("top-level enabled is not false; confirm history features are intentionally enabled")

    feature_sources = data.get("feature_sources", {})
    if not isinstance(feature_sources, dict):
        errors.append("feature_sources must be an object")
        feature_sources = {}

    for name in REQUIRED_FEATURE_SOURCES:
        source = feature_sources.get(name)
        if not isinstance(source, dict):
            errors.append(f"missing feature source: {name}")
            continue

        path = source.get("path")
        if not path:
            errors.append(f"{name}: missing path")
        elif not Path(path).exists():
            errors.append(f"{name}: path does not exist: {path}")

        if source.get("enabled") is not True:
            warnings.append(f"{name}: source enabled is not true")

    racer_source = feature_sources.get("racer_history_features", {})
    if racer_source:
        if racer_source.get("key") != "racer_id":
            errors.append("racer_history_features.key must be racer_id")
        columns = racer_source.get("columns", [])
        for col in ["race_count", "win_rate", "top2_rate", "top3_rate", "avg_start_timing"]:
            if col not in columns:
                errors.append(f"racer_history_features missing column: {col}")

    join_policy = data.get("prediction_join_policy", {})
    if join_policy.get("join_key") != "racer_id":
        errors.append("prediction_join_policy.join_key must be racer_id")
    if join_policy.get("missing_racer_policy") != "use_default_values":
        errors.append("missing_racer_policy must be use_default_values")

    default_values = join_policy.get("default_values", {})
    for col in ["race_count", "win_rate", "top2_rate", "top3_rate"]:
        if col not in default_values:
            errors.append(f"default_values missing: {col}")

    safety = data.get("safety", {})
    if safety.get("affects_prediction_output") is not False:
        errors.append("safety.affects_prediction_output must be false")
    if safety.get("requires_explicit_enable") is not True:
        errors.append("safety.requires_explicit_enable must be true")

    if warnings:
        print("History feature config validation warnings:")
        for warning in warnings:
            print("WARNING: " + warning)

    if errors:
        print("History feature config validation: FAILED")
        for error in errors:
            print("ERROR: " + error)
        raise SystemExit(1)

    print("History feature config validation: OK")
    print("STEP 122 CHECK: OK")


if __name__ == "__main__":
    main()
