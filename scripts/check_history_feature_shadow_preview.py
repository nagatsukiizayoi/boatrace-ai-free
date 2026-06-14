from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PREVIEW_PATH = Path("docs/prediction_history_feature_shadow_preview.json")
PREDICTION_PATH = Path("docs/prediction.json")
CONFIG_PATH = Path("data/history_feature_config.json")

REQUIRED_FALSE_FLAGS = [
    "history_features_enabled",
    "affects_prediction_output",
    "prediction_output_modified",
    "prediction_json_modified",
    "score_modified",
    "rank_modified",
    "recommendation_modified",
    "expected_value_modified",
]

REQUIRED_TOP_LEVEL_KEYS = [
    "schema_version",
    "step",
    "source_prediction",
    "source_adapter",
    "history_features_enabled",
    "affects_prediction_output",
    "prediction_output_modified",
    "prediction_json_modified",
    "score_modified",
    "rank_modified",
    "recommendation_modified",
    "expected_value_modified",
    "candidate_count",
    "unique_racer_id_count",
    "matched_candidate_count",
    "missing_candidate_count",
    "entries",
]

REQUIRED_SHADOW_KEYS = [
    "enabled",
    "available",
    "source",
    "features",
    "affects_prediction_output",
    "prediction_output_modified",
    "prediction_json_modified",
]

REQUIRED_ENTRY_KEYS = [
    "index",
    "candidate",
    "history_feature_shadow",
    "score_unchanged",
    "rank_unchanged",
    "recommendation_unchanged",
    "expected_value_unchanged",
]


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def read_json(path: Path) -> Any:
    if not path.exists():
        fail(f"missing file: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON: {path}: {exc}")


def assert_bool_false(data: dict[str, Any], key: str) -> None:
    if data.get(key) is not False:
        fail(f"{key} must be false")


def assert_non_negative_int(data: dict[str, Any], key: str) -> None:
    value = data.get(key)
    if not isinstance(value, int):
        fail(f"{key} must be int")
    if value < 0:
        fail(f"{key} must be non-negative")


def check_config_disabled() -> None:
    config = read_json(CONFIG_PATH)
    if not isinstance(config, dict):
        fail("history feature config must be object")
    if config.get("enabled") is not False:
        fail("data/history_feature_config.json top-level enabled must be false")


def check_preview(data: Any) -> None:
    if not isinstance(data, dict):
        fail("preview root must be object")

    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in data:
            fail(f"missing top-level key: {key}")

    if data.get("schema_version") != "history_feature_shadow_preview_v1":
        fail("schema_version mismatch")

    if data.get("step") != "STEP141-A":
        fail("step must be STEP141-A")

    if data.get("source_prediction") != "docs/prediction.json":
        fail("source_prediction mismatch")

    if data.get("source_adapter") != "scripts/history_feature_prediction_adapter.py":
        fail("source_adapter mismatch")

    for key in REQUIRED_FALSE_FLAGS:
        assert_bool_false(data, key)

    for key in [
        "candidate_count",
        "unique_racer_id_count",
        "matched_candidate_count",
        "missing_candidate_count",
    ]:
        assert_non_negative_int(data, key)

    entries = data.get("entries")
    if not isinstance(entries, list):
        fail("entries must be list")

    if data["candidate_count"] != len(entries):
        fail("candidate_count must equal len(entries)")

    if data["matched_candidate_count"] + data["missing_candidate_count"] != data["candidate_count"]:
        fail("matched + missing must equal candidate_count")

    for i, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            fail(f"entry {i} must be object")

        for key in REQUIRED_ENTRY_KEYS:
            if key not in entry:
                fail(f"entry {i} missing key: {key}")

        if entry.get("index") != i:
            fail(f"entry {i} index mismatch")

        for key in [
            "score_unchanged",
            "rank_unchanged",
            "recommendation_unchanged",
            "expected_value_unchanged",
        ]:
            if entry.get(key) is not True:
                fail(f"entry {i} {key} must be true")

        shadow = entry.get("history_feature_shadow")
        if not isinstance(shadow, dict):
            fail(f"entry {i} history_feature_shadow must be object")

        for key in REQUIRED_SHADOW_KEYS:
            if key not in shadow:
                fail(f"entry {i} shadow missing key: {key}")

        if shadow.get("enabled") is not False:
            fail(f"entry {i} shadow enabled must be false")

        for key in [
            "affects_prediction_output",
            "prediction_output_modified",
            "prediction_json_modified",
        ]:
            if shadow.get(key) is not False:
                fail(f"entry {i} shadow {key} must be false")

        if not isinstance(shadow.get("features"), dict):
            fail(f"entry {i} shadow features must be object")


def main() -> None:
    if not PREDICTION_PATH.exists():
        fail(f"missing file: {PREDICTION_PATH}")

    check_config_disabled()

    data = read_json(PREVIEW_PATH)
    check_preview(data)

    print("History feature shadow preview validation: OK")
    print("STEP 141-B CHECK: OK")
    print(f"candidate_count={data['candidate_count']}")
    print(f"matched_candidate_count={data['matched_candidate_count']}")
    print(f"missing_candidate_count={data['missing_candidate_count']}")


if __name__ == "__main__":
    main()
