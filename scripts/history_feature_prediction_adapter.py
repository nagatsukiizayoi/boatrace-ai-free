from __future__ import annotations

import json
import sys
import importlib.util
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "data" / "history_feature_config.json"
PREDICTION_PATH = ROOT / "docs" / "prediction.json"
LOADER_PATH = ROOT / "scripts" / "history_feature_loader.py"

ID_KEYS = (
    "racer_id",
    "player_id",
    "racerId",
    "playerId",
    "registration_number",
    "toban",
    "登番",
)

_FEATURE_MAP_CACHE = None
_CONFIG_CACHE = None
_LOADER_CACHE = None


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_config() -> dict[str, Any]:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is None:
        if not CONFIG_PATH.exists():
            raise FileNotFoundError(f"Missing config: {CONFIG_PATH}")
        data = _load_json(CONFIG_PATH)
        if not isinstance(data, dict):
            raise ValueError("history_feature_config.json must be a JSON object")
        _CONFIG_CACHE = data
    return _CONFIG_CACHE


def history_features_enabled() -> bool:
    config = load_config()
    return bool(config.get("enabled", False))


def _load_loader_module():
    global _LOADER_CACHE
    if _LOADER_CACHE is not None:
        return _LOADER_CACHE

    if not LOADER_PATH.exists():
        raise FileNotFoundError(f"Missing loader: {LOADER_PATH}")

    spec = importlib.util.spec_from_file_location("history_feature_loader", LOADER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load history_feature_loader module spec")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _LOADER_CACHE = module
    return module


def normalize_racer_id(value: Any) -> str | None:
    if value is None:
        return None

    if isinstance(value, bool):
        return None

    if isinstance(value, int):
        return str(value)

    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        text = str(value).strip()
        return text or None

    text = str(value).strip()
    if not text:
        return None

    if text.endswith(".0"):
        head = text[:-2]
        if head.isdigit():
            return head

    return text


def extract_racer_id(candidate: Any) -> str | None:
    if isinstance(candidate, dict):
        for key in ID_KEYS:
            if key in candidate:
                racer_id = normalize_racer_id(candidate.get(key))
                if racer_id:
                    return racer_id

    return normalize_racer_id(candidate)


def _find_default_values(obj: Any) -> dict[str, Any] | None:
    if isinstance(obj, dict):
        if isinstance(obj.get("default_values"), dict):
            return obj["default_values"]

        for value in obj.values():
            found = _find_default_values(value)
            if found is not None:
                return found

    elif isinstance(obj, list):
        for value in obj:
            found = _find_default_values(value)
            if found is not None:
                return found

    return None


def get_default_values() -> dict[str, Any]:
    config = load_config()

    join_policy = config.get("prediction_join_policy")
    if isinstance(join_policy, dict) and isinstance(join_policy.get("default_values"), dict):
        return dict(join_policy["default_values"])

    defaults = config.get("default_values")
    if isinstance(defaults, dict):
        return dict(defaults)

    found = _find_default_values(config)
    if found is not None:
        return dict(found)

    return {
        "race_count": 0,
        "win_rate": 0.0,
        "top2_rate": 0.0,
        "top3_rate": 0.0,
        "avg_start_timing": 0.0,
    }


def _normalize_feature_map(raw_map: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(raw_map, dict):
        raise ValueError("load_racer_history_features() must return a dict")

    result: dict[str, dict[str, Any]] = {}

    for key, value in raw_map.items():
        racer_id = normalize_racer_id(key)
        if not racer_id:
            continue

        if isinstance(value, dict):
            item = dict(value)
        else:
            item = {"value": value}

        result[racer_id] = item

    return result


def load_feature_map() -> dict[str, dict[str, Any]]:
    global _FEATURE_MAP_CACHE

    if _FEATURE_MAP_CACHE is not None:
        return _FEATURE_MAP_CACHE

    loader = _load_loader_module()

    if not hasattr(loader, "load_racer_history_features"):
        raise AttributeError("history_feature_loader.py must define load_racer_history_features")

    raw = loader.load_racer_history_features()
    _FEATURE_MAP_CACHE = _normalize_feature_map(raw)
    return _FEATURE_MAP_CACHE


def _safe_feature_dict(features: Any) -> dict[str, Any]:
    if isinstance(features, dict):
        return dict(features)
    return {}


def get_history_feature_preview(candidate_or_id: Any) -> dict[str, Any]:
    racer_id = extract_racer_id(candidate_or_id)
    enabled = history_features_enabled()

    base = {
        "history_features_enabled": enabled,
        "affects_prediction_output": False,
        "prediction_output_modified": False,
    }

    if not racer_id:
        defaults = get_default_values()
        return {
            **base,
            "racer_id": None,
            "history_feature_available": False,
            "history_feature_source": "default_values",
            "features": defaults,
        }

    feature_map = load_feature_map()
    features = feature_map.get(racer_id)

    if features is not None:
        return {
            **base,
            "racer_id": racer_id,
            "history_feature_available": True,
            "history_feature_source": "racer_history_features.csv",
            "features": _safe_feature_dict(features),
        }

    loader = _load_loader_module()
    if hasattr(loader, "get_racer_history_feature"):
        try:
            loaded = loader.get_racer_history_feature(racer_id)
            if isinstance(loaded, dict):
                available = bool(loaded.get("history_feature_available", False))
                source = loaded.get(
                    "history_feature_source",
                    "racer_history_features.csv" if available else "default_values",
                )
                copied = dict(loaded)
                copied.update(base)
                copied.setdefault("racer_id", racer_id)
                copied.setdefault("history_feature_available", available)
                copied.setdefault("history_feature_source", source)
                copied.setdefault("features", get_default_values() if not available else loaded)
                return copied
        except Exception:
            pass

    defaults = get_default_values()
    return {
        **base,
        "racer_id": racer_id,
        "history_feature_available": False,
        "history_feature_source": "default_values",
        "features": defaults,
    }


def attach_history_feature_preview(candidate: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(candidate, dict):
        raise TypeError("candidate must be a dict")

    copied = dict(candidate)
    copied["history_feature_preview"] = get_history_feature_preview(candidate)
    return copied


def _walk_dicts(obj: Any, limit: int = 50) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []

    def walk(value: Any) -> None:
        if len(found) >= limit:
            return

        if isinstance(value, dict):
            if extract_racer_id(value):
                found.append(value)
            for child in value.values():
                walk(child)

        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(obj)
    return found


def build_history_feature_context(prediction: dict[str, Any], limit: int = 50) -> dict[str, Any]:
    if not isinstance(prediction, dict):
        raise TypeError("prediction must be a dict")

    candidates = _walk_dicts(prediction, limit=limit)
    previews = [get_history_feature_preview(candidate) for candidate in candidates]

    matched = sum(1 for item in previews if item.get("history_feature_available") is True)
    missing = sum(1 for item in previews if item.get("history_feature_available") is False)

    return {
        "history_features_enabled": history_features_enabled(),
        "affects_prediction_output": False,
        "prediction_output_modified": False,
        "candidate_count": len(candidates),
        "matched_candidate_count": matched,
        "missing_candidate_count": missing,
        "feature_map_racer_count": len(load_feature_map()),
        "previews": previews,
    }


def main() -> int:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(CONFIG_PATH)

    config = load_config()
    enabled = history_features_enabled()
    feature_map = load_feature_map()

    print(f"config_path: {CONFIG_PATH}")
    print(f"history_features_enabled: {enabled}")
    print(f"loaded_feature_racer_count: {len(feature_map)}")

    if enabled is not False:
        raise AssertionError("STEP137-D requires top-level enabled:false")

    missing_preview = get_history_feature_preview("__missing_racer_id_for_adapter_check__")
    print(f"missing_history_feature_available: {missing_preview.get('history_feature_available')}")
    print(f"missing_history_feature_source: {missing_preview.get('history_feature_source')}")

    if missing_preview.get("affects_prediction_output") is not False:
        raise AssertionError("affects_prediction_output must be false")

    if missing_preview.get("prediction_output_modified") is not False:
        raise AssertionError("prediction_output_modified must be false")

    if PREDICTION_PATH.exists():
        prediction = _load_json(PREDICTION_PATH)
        if isinstance(prediction, dict):
            context = build_history_feature_context(prediction, limit=20)
            print(f"prediction_candidate_count: {context['candidate_count']}")
            print(f"prediction_matched_candidate_count: {context['matched_candidate_count']}")
            print(f"prediction_missing_candidate_count: {context['missing_candidate_count']}")

    print("History feature prediction adapter dry-run: OK")
    print("STEP 137-D CHECK: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
