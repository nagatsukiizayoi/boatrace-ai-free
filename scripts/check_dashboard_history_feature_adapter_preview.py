from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

INDEX_PATH = ROOT / "docs" / "index.html"
PREVIEW_PATH = ROOT / "docs" / "prediction_history_feature_adapter_preview.json"
CONFIG_PATH = ROOT / "data" / "history_feature_config.json"


REQUIRED_HTML_FRAGMENTS = [
    "history-feature-adapter-preview-section",
    "prediction_history_feature_adapter_preview.json",
    "履歴特徴量 adapter preview",
    "hfap-enabled",
    "hfap-affects",
    "hfap-modified",
    "hfap-json-modified",
    "hfap-candidate-count",
    "hfap-matched-count",
    "hfap-missing-count",
    "hfap-loaded-count",
]


REQUIRED_PREVIEW_KEYS = [
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


def main() -> int:
    require(INDEX_PATH.exists(), f"Missing dashboard index: {INDEX_PATH}")
    require(PREVIEW_PATH.exists(), f"Missing adapter preview JSON: {PREVIEW_PATH}")
    require(CONFIG_PATH.exists(), f"Missing config JSON: {CONFIG_PATH}")

    html = INDEX_PATH.read_text(encoding="utf-8")
    preview = load_json(PREVIEW_PATH)
    config = load_json(CONFIG_PATH)

    require(isinstance(preview, dict), "adapter preview JSON must be object")
    require(isinstance(config, dict), "config JSON must be object")

    missing_fragments = [fragment for fragment in REQUIRED_HTML_FRAGMENTS if fragment not in html]
    require(not missing_fragments, f"index.html missing fragments: {missing_fragments}")

    missing_keys = [key for key in REQUIRED_PREVIEW_KEYS if key not in preview]
    require(not missing_keys, f"adapter preview missing keys: {missing_keys}")

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
        require(isinstance(preview.get(key), int), f"{key} must be int")
        require(preview.get(key) >= 0, f"{key} must be >= 0")

    require(isinstance(preview.get("entries"), list), "entries must be list")

    print(f"index_path: {INDEX_PATH}")
    print(f"preview_path: {PREVIEW_PATH}")
    print(f"candidate_count: {preview.get('candidate_count')}")
    print(f"matched_candidate_count: {preview.get('matched_candidate_count')}")
    print(f"missing_candidate_count: {preview.get('missing_candidate_count')}")
    print("Dashboard history feature adapter preview validation: OK")
    print("STEP 138-A CHECK: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
