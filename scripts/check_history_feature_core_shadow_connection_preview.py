from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


EXPORTER_PATH = Path("scripts/export_history_feature_core_shadow_connection_preview.py")
PREVIEW_PATH = Path("docs/prediction_history_feature_core_shadow_connection_preview.json")
CONFIG_PATH = Path("data/history_feature_config.json")
PREDICTION_PATH = Path("docs/prediction.json")


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    sys.exit(1)


def load_json(path: Path):
    if not path.exists():
        fail(f"missing file: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON: {path}: {exc}")


def require_key(data: dict, key: str):
    if key not in data:
        fail(f"missing required key: {key}")
    return data.get(key)


def require_false(data: dict, key: str) -> None:
    value = require_key(data, key)
    if value is not False:
        fail(f"{key} must be false, got {value!r}")


def optional_false(data: dict, key: str) -> None:
    if key in data and data.get(key) is not False:
        fail(f"{key} must be false when present, got {data.get(key)!r}")


def optional_true(data: dict, key: str) -> None:
    if key in data and data.get(key) is not True:
        fail(f"{key} must be true when present, got {data.get(key)!r}")


def require_nonnegative_int(data: dict, key: str) -> int:
    value = require_key(data, key)
    if not isinstance(value, int):
        fail(f"{key} must be int, got {type(value).__name__}: {value!r}")
    if value < 0:
        fail(f"{key} must be non-negative, got {value}")
    return value


def optional_nonnegative_int(data: dict, key: str) -> None:
    if key not in data:
        return
    value = data.get(key)
    if not isinstance(value, int):
        fail(f"{key} must be int when present, got {type(value).__name__}: {value!r}")
    if value < 0:
        fail(f"{key} must be non-negative when present, got {value}")


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
        fail(f"git diff check failed for docs/prediction.json: {result.stderr.strip()}")


def main() -> None:
    if not EXPORTER_PATH.exists():
        fail(f"missing exporter script: {EXPORTER_PATH}")

    data = load_json(PREVIEW_PATH)
    config = load_json(CONFIG_PATH)

    if config.get("enabled") is not False:
        fail(f"data/history_feature_config.json enabled must be false, got {config.get('enabled')!r}")

    step = require_key(data, "step")
    if step != "STEP146-A":
        fail(f"step must be STEP146-A, got {step!r}")

    connection_mode = require_key(data, "connection_mode")
    if connection_mode != "shadow-only":
        fail(f"connection_mode must be shadow-only, got {connection_mode!r}")

    require_false(data, "core_connection_enabled")
    require_false(data, "affects_prediction_output")
    require_false(data, "history_features_enabled")

    optional_true(data, "safe_mode")
    optional_false(data, "writes_prediction_json")
    optional_false(data, "writes_generated_outputs")
    optional_false(data, "expected_value_changed")
    optional_false(data, "prediction_score_changed")
    optional_false(data, "rank_changed")
    optional_false(data, "recommendation_changed")

    candidate_count = require_nonnegative_int(data, "candidate_count")
    matched_candidate_count = require_nonnegative_int(data, "matched_candidate_count")
    missing_candidate_count = require_nonnegative_int(data, "missing_candidate_count")

    optional_nonnegative_int(data, "prediction_candidate_count")
    optional_nonnegative_int(data, "shadow_candidate_count")

    if matched_candidate_count + missing_candidate_count != candidate_count:
        fail(
            "candidate count mismatch: "
            f"candidate_count={candidate_count}, "
            f"matched_candidate_count={matched_candidate_count}, "
            f"missing_candidate_count={missing_candidate_count}"
        )

    check_prediction_json_unchanged()

    print("History feature core shadow connection preview validation: OK")
    print("STEP 146-B CHECK: OK")
    print(f"output={PREVIEW_PATH}")
    print(f"step={step}")
    print(f"connection_mode={connection_mode}")
    print(f"core_connection_enabled={data.get('core_connection_enabled')}")
    print(f"affects_prediction_output={data.get('affects_prediction_output')}")
    print(f"history_features_enabled={data.get('history_features_enabled')}")
    print(f"candidate_count={candidate_count}")
    print(f"matched_candidate_count={matched_candidate_count}")
    print(f"missing_candidate_count={missing_candidate_count}")


if __name__ == "__main__":
    main()
