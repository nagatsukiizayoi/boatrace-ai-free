from __future__ import annotations

import json
import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PREDICTION_PATH = ROOT / "docs" / "prediction.json"
OUTPUT_PATH = ROOT / "docs" / "prediction_history_feature_adapter_preview.json"
ADAPTER_PATH = ROOT / "scripts" / "history_feature_prediction_adapter.py"
CONFIG_PATH = ROOT / "data" / "history_feature_config.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_adapter():
    if not ADAPTER_PATH.exists():
        raise FileNotFoundError(f"Missing adapter: {ADAPTER_PATH}")

    spec = importlib.util.spec_from_file_location("history_feature_prediction_adapter", ADAPTER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load adapter module")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def collect_candidate_dicts(adapter, obj: Any, limit: int = 80) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []

    def walk(value: Any) -> None:
        if len(found) >= limit:
            return

        if isinstance(value, dict):
            if adapter.extract_racer_id(value):
                found.append(value)

            for child in value.values():
                walk(child)

        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(obj)
    return found


def slim_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    keep_keys = [
        "racer_id",
        "player_id",
        "racerId",
        "playerId",
        "registration_number",
        "toban",
        "登番",
        "name",
        "racer_name",
        "player_name",
        "rank",
        "score",
        "confidence",
        "course",
    ]

    slim: dict[str, Any] = {}
    for key in keep_keys:
        if key in candidate:
            slim[key] = candidate[key]
    return slim


def main() -> int:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing config: {CONFIG_PATH}")

    if not PREDICTION_PATH.exists():
        raise FileNotFoundError(f"Missing prediction JSON: {PREDICTION_PATH}")

    adapter = load_adapter()
    prediction = load_json(PREDICTION_PATH)

    if not isinstance(prediction, dict):
        raise ValueError("docs/prediction.json must be a JSON object")

    enabled = adapter.history_features_enabled()
    if enabled is not False:
        raise AssertionError("STEP137-F requires history features enabled:false")

    feature_map = adapter.load_feature_map()
    candidates = collect_candidate_dicts(adapter, prediction, limit=80)

    entries: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for idx, candidate in enumerate(candidates):
        racer_id = adapter.extract_racer_id(candidate)
        preview = adapter.get_history_feature_preview(candidate)

        if racer_id:
            seen_ids.add(racer_id)

        features = preview.get("features")
        if isinstance(features, dict):
            feature_keys = sorted(features.keys())
            feature_sample = {key: features.get(key) for key in feature_keys[:10]}
        else:
            feature_keys = []
            feature_sample = {}

        entries.append(
            {
                "index": idx,
                "racer_id": racer_id,
                "candidate": slim_candidate(candidate),
                "history_feature_available": preview.get("history_feature_available"),
                "history_feature_source": preview.get("history_feature_source"),
                "history_features_enabled": preview.get("history_features_enabled"),
                "affects_prediction_output": preview.get("affects_prediction_output"),
                "prediction_output_modified": preview.get("prediction_output_modified"),
                "feature_key_count": len(feature_keys),
                "feature_keys": feature_keys[:30],
                "feature_sample": feature_sample,
            }
        )

    matched = sum(1 for item in entries if item.get("history_feature_available") is True)
    missing = sum(1 for item in entries if item.get("history_feature_available") is False)

    output = {
        "version": "1.0",
        "step": "STEP137-F",
        "description": "Dry-run adapter preview for history features. This file does not affect prediction output.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_prediction": "docs/prediction.json",
        "source_config": "data/history_feature_config.json",
        "source_adapter": "scripts/history_feature_prediction_adapter.py",
        "history_features_enabled": enabled,
        "affects_prediction_output": False,
        "prediction_output_modified": False,
        "prediction_json_modified": False,
        "candidate_count": len(candidates),
        "unique_racer_id_count": len(seen_ids),
        "matched_candidate_count": matched,
        "missing_candidate_count": missing,
        "loaded_feature_racer_count": len(feature_map),
        "entries": entries,
    }

    write_json(OUTPUT_PATH, output)

    print(f"output_path: {OUTPUT_PATH}")
    print(f"candidate_count: {len(candidates)}")
    print(f"unique_racer_id_count: {len(seen_ids)}")
    print(f"matched_candidate_count: {matched}")
    print(f"missing_candidate_count: {missing}")
    print(f"loaded_feature_racer_count: {len(feature_map)}")
    print("History feature adapter preview export: OK")
    print("STEP 137-F CHECK: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
