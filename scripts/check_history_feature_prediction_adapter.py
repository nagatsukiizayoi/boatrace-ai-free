from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = ROOT / "scripts" / "history_feature_prediction_adapter.py"
CONFIG_PATH = ROOT / "data" / "history_feature_config.json"
PREDICTION_PATH = ROOT / "docs" / "prediction.json"


def load_adapter():
    if not ADAPTER_PATH.exists():
        raise FileNotFoundError(f"Missing adapter: {ADAPTER_PATH}")

    spec = importlib.util.spec_from_file_location("history_feature_prediction_adapter", ADAPTER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load adapter module spec")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assert_equal(actual, expected, message):
    if actual != expected:
        raise AssertionError(f"{message}: expected {expected!r}, got {actual!r}")


def assert_false(value, message):
    if value is not False:
        raise AssertionError(f"{message}: expected False, got {value!r}")


def main() -> int:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing config: {CONFIG_PATH}")

    if not PREDICTION_PATH.exists():
        raise FileNotFoundError(f"Missing prediction JSON: {PREDICTION_PATH}")

    adapter = load_adapter()

    assert_false(adapter.history_features_enabled(), "top-level history feature enabled flag")

    assert_equal(adapter.normalize_racer_id(None), None, "None normalization")
    assert_equal(adapter.normalize_racer_id(""), None, "empty string normalization")
    assert_equal(adapter.normalize_racer_id(" 1234 "), "1234", "string trim normalization")
    assert_equal(adapter.normalize_racer_id(1234), "1234", "integer normalization")
    assert_equal(adapter.normalize_racer_id(1234.0), "1234", "float integer normalization")

    assert_equal(adapter.extract_racer_id({"racer_id": "1111"}), "1111", "racer_id extraction")
    assert_equal(adapter.extract_racer_id({"player_id": "2222"}), "2222", "player_id extraction")
    assert_equal(adapter.extract_racer_id({"racerId": "3333"}), "3333", "racerId extraction")
    assert_equal(adapter.extract_racer_id({"playerId": "4444"}), "4444", "playerId extraction")
    assert_equal(adapter.extract_racer_id({"registration_number": "5555"}), "5555", "registration_number extraction")
    assert_equal(adapter.extract_racer_id({"toban": "6666"}), "6666", "toban extraction")
    assert_equal(adapter.extract_racer_id({"登番": "7777"}), "7777", "Japanese key extraction")

    feature_map = adapter.load_feature_map()
    if not isinstance(feature_map, dict):
        raise AssertionError("feature map must be dict")

    if len(feature_map) <= 0:
        raise AssertionError("feature map must not be empty")

    missing = adapter.get_history_feature_preview("__missing_racer_id_for_adapter_check__")
    assert_false(missing.get("history_features_enabled"), "missing preview enabled flag")
    assert_false(missing.get("affects_prediction_output"), "missing preview affects flag")
    assert_false(missing.get("prediction_output_modified"), "missing preview modified flag")
    assert_equal(missing.get("history_feature_available"), False, "missing preview availability")
    assert_equal(missing.get("history_feature_source"), "default_values", "missing preview source")

    sample_racer_id = next(iter(feature_map.keys()))
    sample = adapter.get_history_feature_preview(sample_racer_id)

    assert_false(sample.get("history_features_enabled"), "sample preview enabled flag")
    assert_false(sample.get("affects_prediction_output"), "sample preview affects flag")
    assert_false(sample.get("prediction_output_modified"), "sample preview modified flag")

    if sample.get("history_feature_available") is not True:
        raise AssertionError("sample racer should have available history feature")

    candidate = {"racer_id": sample_racer_id, "name": "adapter-check-sample"}
    attached = adapter.attach_history_feature_preview(candidate)

    if "history_feature_preview" not in attached:
        raise AssertionError("attached candidate must include history_feature_preview")

    if "history_feature_preview" in candidate:
        raise AssertionError("attach_history_feature_preview must not mutate original candidate")

    prediction = adapter._load_json(PREDICTION_PATH)
    if isinstance(prediction, dict):
        context = adapter.build_history_feature_context(prediction, limit=20)
        assert_false(context.get("history_features_enabled"), "context enabled flag")
        assert_false(context.get("affects_prediction_output"), "context affects flag")
        assert_false(context.get("prediction_output_modified"), "context modified flag")

        if "candidate_count" not in context:
            raise AssertionError("context must include candidate_count")

        if "feature_map_racer_count" not in context:
            raise AssertionError("context must include feature_map_racer_count")

    print(f"adapter_path: {ADAPTER_PATH}")
    print(f"feature_map_racer_count: {len(feature_map)}")
    print(f"sample_racer_id: {sample_racer_id}")
    print("History feature prediction adapter validation: OK")
    print("STEP 137-D CHECK: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
