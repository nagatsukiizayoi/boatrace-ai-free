from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

PREVIEW_PATH = ROOT / "docs" / "prediction_history_feature_adapter_preview.json"
CONFIG_PATH = ROOT / "data" / "history_feature_config.json"
PREDICTION_PATH = ROOT / "docs" / "prediction.json"
ADAPTER_PATH = ROOT / "scripts" / "history_feature_prediction_adapter.py"
EXPORT_PATH = ROOT / "scripts" / "export_history_feature_adapter_preview.py"


REQUIRED_TOP_LEVEL_KEYS = [
    "version",
    "step",
    "description",
    "generated_at",
    "source_prediction",
    "source_config",
    "source_adapter",
    "history_features_enabled",
    "affects_prediction_output",
    "prediction_output_modified",
    "prediction_json_modified",
    "candidate_count",
    "unique_racer_id_count",
    "matched_candidate_count",
    "missing_candidate_count",
    "loaded_feature_racer_count",
    "entries",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_false(value: Any, message: str) -> None:
    require(value is False, f"{message}: expected false, got {value!r}")


def require_int(value: Any, key: str) -> None:
    require(isinstance(value, int), f"{key} must be int")
    require(value >= 0, f"{key} must be >= 0")


def main() -> int:
    for path in [PREVIEW_PATH, CONFIG_PATH, PREDICTION_PATH, ADAPTER_PATH, EXPORT_PATH]:
        require(path.exists(), f"Missing required file: {path}")

    preview = load_json(PREVIEW_PATH)
    config = load_json(CONFIG_PATH)

    require(isinstance(preview, dict), "preview JSON must be object")
    require(isinstance(config, dict), "config JSON must be object")

    missing_keys = [key for key in REQUIRED_TOP_LEVEL_KEYS if key not in preview]
    require(not missing_keys, f"preview JSON missing keys: {missing_keys}")

    require(preview.get("step") == "STEP137-F", "step must be STEP137-F")
    require(preview.get("source_prediction") == "docs/prediction.json", "source_prediction mismatch")
    require(preview.get("source_config") == "data/history_feature_config.json", "source_config mismatch")
    require(preview.get("source_adapter") == "scripts/history_feature_prediction_adapter.py", "source_adapter mismatch")

    require_false(config.get("enabled"), "config enabled")
    require_false(preview.get("history_features_enabled"), "preview history_features_enabled")
    require_false(preview.get("affects_prediction_output"), "preview affects_prediction_output")
    require_false(preview.get("prediction_output_modified"), "preview prediction_output_modified")
    require_false(preview.get("prediction_json_modified"), "preview prediction_json_modified")

    for key in [
        "candidate_count",
        "unique_racer_id_count",
        "matched_candidate_count",
        "missing_candidate_count",
        "loaded_feature_racer_count",
    ]:
        require_int(preview.get(key), key)

    entries = preview.get("entries")
    require(isinstance(entries, list), "entries must be list")
    require(len(entries) == preview.get("candidate_count"), "entries length must match candidate_count")

    require(
        preview.get("loaded_feature_racer_count", 0) > 0,
        "loaded_feature_racer_count must be > 0",
    )

    if entries:
        first = entries[0]
        require(isinstance(first, dict), "entry must be object")

        for key in [
            "index",
            "racer_id",
            "candidate",
            "history_feature_available",
            "history_feature_source",
            "history_features_enabled",
            "affects_prediction_output",
            "prediction_output_modified",
            "feature_key_count",
            "feature_keys",
            "feature_sample",
        ]:
            require(key in first, f"entry missing key: {key}")

        require_false(first.get("history_features_enabled"), "entry history_features_enabled")
        require_false(first.get("affects_prediction_output"), "entry affects_prediction_output")
        require_false(first.get("prediction_output_modified"), "entry prediction_output_modified")
        require(isinstance(first.get("candidate"), dict), "entry candidate must be object")
        require(isinstance(first.get("feature_keys"), list), "entry feature_keys must be list")
        require(isinstance(first.get("feature_sample"), dict), "entry feature_sample must be object")

    print(f"preview_path: {PREVIEW_PATH}")
    print(f"candidate_count: {preview.get('candidate_count')}")
    print(f"matched_candidate_count: {preview.get('matched_candidate_count')}")
    print(f"missing_candidate_count: {preview.get('missing_candidate_count')}")
    print(f"loaded_feature_racer_count: {preview.get('loaded_feature_racer_count')}")
    print("History feature adapter preview validation: OK")
    print("STEP 137-G CHECK: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
