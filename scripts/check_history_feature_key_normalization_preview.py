from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


CONFIG_PATH = Path("data/history_feature_config.json")
PREDICTION_PATH = Path("docs/prediction.json")
EXPORTER_PATH = Path("scripts/export_history_feature_key_normalization_preview.py")
PREVIEW_PATH = Path("docs/prediction_history_feature_key_normalization_preview.json")


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    sys.exit(1)


def load_json(path: Path) -> Any:
    if not path.exists():
        fail(f"missing file: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON: {path}: {exc}")


def require_key(data: dict[str, Any], key: str) -> Any:
    if key not in data:
        fail(f"missing required key: {key}")
    return data[key]


def require_value(data: dict[str, Any], key: str, expected: Any) -> Any:
    value = require_key(data, key)
    if value != expected:
        fail(f"{key} must be {expected!r}, got {value!r}")
    return value


def require_false(data: dict[str, Any], key: str) -> None:
    value = require_key(data, key)
    if value is not False:
        fail(f"{key} must be False, got {value!r}")


def require_true(data: dict[str, Any], key: str) -> None:
    value = require_key(data, key)
    if value is not True:
        fail(f"{key} must be True, got {value!r}")


def optional_false(data: dict[str, Any], key: str) -> None:
    if key in data and data[key] is not False:
        fail(f"{key} must be False when present, got {data[key]!r}")


def optional_true(data: dict[str, Any], key: str) -> None:
    if key in data and data[key] is not True:
        fail(f"{key} must be True when present, got {data[key]!r}")


def require_dict(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = require_key(data, key)
    if not isinstance(value, dict):
        fail(f"{key} must be dict, got {type(value).__name__}")
    return value


def require_list(data: dict[str, Any], key: str) -> list[Any]:
    value = require_key(data, key)
    if not isinstance(value, list):
        fail(f"{key} must be list, got {type(value).__name__}")
    return value


def require_nonnegative_int(data: dict[str, Any], key: str) -> int:
    value = require_key(data, key)
    if not isinstance(value, int) or value < 0:
        fail(f"{key} must be non-negative int, got {value!r}")
    return value


def optional_nonnegative_int(data: dict[str, Any], key: str) -> None:
    if key in data:
        value = data[key]
        if value is None:
            return
        if not isinstance(value, int) or value < 0:
            fail(f"{key} must be non-negative int when present, got {value!r}")


def check_prediction_json_unchanged() -> None:
    if not PREDICTION_PATH.exists():
        fail(f"missing file: {PREDICTION_PATH}")

    result = subprocess.run(
        ["git", "diff", "--quiet", "--", str(PREDICTION_PATH)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode == 1:
        fail("docs/prediction.json has uncommitted diff")

    if result.returncode not in (0, 1):
        fail(f"git diff check failed: {result.stderr.strip()}")


def main() -> None:
    if not EXPORTER_PATH.exists():
        fail(f"missing exporter script: {EXPORTER_PATH}")

    config = load_json(CONFIG_PATH)
    preview = load_json(PREVIEW_PATH)

    if not isinstance(config, dict):
        fail(f"{CONFIG_PATH} must contain JSON object")

    if not isinstance(preview, dict):
        fail(f"{PREVIEW_PATH} must contain JSON object")

    if config.get("enabled") is not False:
        fail(f"data/history_feature_config.json enabled must be False, got {config.get('enabled')!r}")

    require_value(preview, "step", "STEP148-A")
    require_value(preview, "preview_type", "candidate-key-normalization")
    require_value(preview, "connection_mode", "shadow-only")

    require_false(preview, "config_enabled")
    require_false(preview, "core_connection_enabled")
    require_false(preview, "affects_prediction_output")
    require_false(preview, "writes_prediction_json")
    require_false(preview, "history_features_enabled")
    require_false(preview, "prediction_core_connected")

    optional_true(preview, "safe_mode")
    optional_false(preview, "writes_generated_outputs")
    optional_false(preview, "expected_value_changed")
    optional_false(preview, "prediction_score_changed")
    optional_false(preview, "rank_changed")
    optional_false(preview, "recommendation_changed")

    source_files = require_dict(preview, "source_files")
    expected_source_files = {
        "config": str(CONFIG_PATH),
        "prediction": str(PREDICTION_PATH),
        "core_shadow_connection_preview": "docs/prediction_history_feature_core_shadow_connection_preview.json",
    }

    for key, expected in expected_source_files.items():
        value = source_files.get(key)
        if value != expected:
            fail(f"source_files.{key} must be {expected!r}, got {value!r}")

    output_file = require_key(preview, "output_file")
    if output_file != str(PREVIEW_PATH):
        fail(f"output_file must be {str(PREVIEW_PATH)!r}, got {output_file!r}")

    original_counts = require_dict(preview, "original_core_shadow_preview_counts")
    optional_nonnegative_int(original_counts, "candidate_count")
    optional_nonnegative_int(original_counts, "prediction_candidate_count")
    optional_nonnegative_int(original_counts, "shadow_candidate_count")
    optional_nonnegative_int(original_counts, "matched_candidate_count")
    optional_nonnegative_int(original_counts, "missing_candidate_count")

    normalization_rules = require_list(preview, "normalization_rules")
    if len(normalization_rules) == 0:
        fail("normalization_rules must not be empty")

    counts = require_dict(preview, "normalization_preview_counts")
    prediction_key_count = require_nonnegative_int(counts, "prediction_key_count")
    shadow_key_count = require_nonnegative_int(counts, "shadow_key_count")
    matched_after_normalization_count = require_nonnegative_int(counts, "matched_after_normalization_count")

    if matched_after_normalization_count > prediction_key_count:
        fail(
            "matched_after_normalization_count must not exceed prediction_key_count: "
            f"{matched_after_normalization_count} > {prediction_key_count}"
        )

    if matched_after_normalization_count > shadow_key_count:
        fail(
            "matched_after_normalization_count must not exceed shadow_key_count: "
            f"{matched_after_normalization_count} > {shadow_key_count}"
        )

    matched_sample = require_list(preview, "matched_normalized_keys_sample")
    if len(matched_sample) > 50:
        fail(f"matched_normalized_keys_sample must contain at most 50 items, got {len(matched_sample)}")

    samples = require_list(preview, "normalization_samples")
    for index, item in enumerate(samples[:100]):
        if not isinstance(item, dict):
            fail(f"normalization_samples[{index}] must be dict")
        if "source" not in item:
            fail(f"normalization_samples[{index}] missing source")
        if item.get("source") not in ("prediction", "shadow"):
            fail(f"normalization_samples[{index}].source must be prediction or shadow, got {item.get('source')!r}")
        if "original_candidate_key" not in item:
            fail(f"normalization_samples[{index}] missing original_candidate_key")
        if "normalized_candidate_key" not in item:
            fail(f"normalization_samples[{index}] missing normalized_candidate_key")
        if "match_after_normalization" not in item:
            fail(f"normalization_samples[{index}] missing match_after_normalization")
        if not isinstance(item.get("match_after_normalization"), bool):
            fail(
                f"normalization_samples[{index}].match_after_normalization must be bool, "
                f"got {item.get('match_after_normalization')!r}"
            )

    decision = require_dict(preview, "decision")
    require_true(decision, "matched_candidate_count_zero_is_allowed_in_shadow_only_preview")
    require_true(decision, "do_not_enable_history_features")
    require_true(decision, "do_not_connect_prediction_core")
    require_true(decision, "do_not_modify_prediction_json")

    check_prediction_json_unchanged()

    print("History feature key normalization preview validation: OK")
    print("STEP 148-B CHECK: OK")
    print(f"output={PREVIEW_PATH}")
    print("step=STEP148-A")
    print("preview_type=candidate-key-normalization")
    print("connection_mode=shadow-only")
    print("config_enabled=False")
    print("core_connection_enabled=False")
    print("affects_prediction_output=False")
    print("writes_prediction_json=False")
    print("history_features_enabled=False")
    print("prediction_core_connected=False")
    print(f"prediction_key_count={prediction_key_count}")
    print(f"shadow_key_count={shadow_key_count}")
    print(f"matched_after_normalization_count={matched_after_normalization_count}")


if __name__ == "__main__":
    main()
