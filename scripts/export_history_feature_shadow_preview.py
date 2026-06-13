from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from history_feature_prediction_adapter import (
    attach_history_feature_preview,
    load_config,
)

PREDICTION_PATH = Path("docs/prediction.json")
OUTPUT_PATH = Path("docs/prediction_history_feature_shadow_preview.json")
CONFIG_PATH = Path("data/history_feature_config.json")

DEFAULT_FEATURES = {
    "race_count": 0,
    "win_rate": 0.0,
    "top2_rate": 0.0,
    "top3_rate": 0.0,
    "avg_start_timing": 0.0,
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def collect_prediction_candidates(prediction: Any) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []

    if isinstance(prediction, dict):
        for key in ("recommendations", "predictions", "candidates", "entries"):
            for item in as_list(prediction.get(key)):
                if isinstance(item, dict):
                    candidates.append(item)

        for race in as_list(prediction.get("races")):
            if not isinstance(race, dict):
                continue
            for key in ("recommendations", "predictions", "candidates", "entries"):
                for item in as_list(race.get(key)):
                    if isinstance(item, dict):
                        merged = dict(item)
                        merged.setdefault("race_id", race.get("race_id"))
                        merged.setdefault("race_no", race.get("race_no"))
                        merged.setdefault("venue_name", race.get("venue_name"))
                        candidates.append(merged)

    elif isinstance(prediction, list):
        for item in prediction:
            if isinstance(item, dict):
                candidates.append(item)

    return candidates


def normalize_shadow(attached: dict[str, Any]) -> dict[str, Any]:
    preview = attached.get("history_feature_preview")
    if not isinstance(preview, dict):
        preview = {}

    features = preview.get("features")
    if not isinstance(features, dict):
        features = dict(DEFAULT_FEATURES)

    return {
        "enabled": False,
        "available": bool(preview.get("available", False)),
        "source": preview.get("source") or "default_values",
        "features": features,
        "affects_prediction_output": False,
        "prediction_output_modified": False,
        "prediction_json_modified": False,
    }


def build_shadow_entry(candidate: dict[str, Any], index: int) -> dict[str, Any]:
    base = deepcopy(candidate)
    attached = attach_history_feature_preview(base)
    shadow = normalize_shadow(attached)

    return {
        "index": index,
        "race_id": base.get("race_id"),
        "race_no": base.get("race_no"),
        "venue_name": base.get("venue_name"),
        "racer_id": attached.get("racer_id"),
        "candidate": base,
        "history_feature_shadow": shadow,
        "score_unchanged": True,
        "rank_unchanged": True,
        "recommendation_unchanged": True,
        "expected_value_unchanged": True,
    }


def main() -> None:
    config = load_config()
    enabled = bool(config.get("enabled", False))

    prediction = read_json(PREDICTION_PATH)
    candidates = collect_prediction_candidates(prediction)

    entries = [build_shadow_entry(candidate, i + 1) for i, candidate in enumerate(candidates)]

    matched = sum(1 for e in entries if e["history_feature_shadow"]["available"])
    missing = len(entries) - matched
    unique_racer_ids = sorted(
        {
            str(e.get("racer_id"))
            for e in entries
            if e.get("racer_id") not in (None, "")
        }
    )

    output = {
        "schema_version": "history_feature_shadow_preview_v1",
        "step": "STEP141-A",
        "source_prediction": str(PREDICTION_PATH),
        "source_adapter": "scripts/history_feature_prediction_adapter.py",
        "history_features_enabled": enabled,
        "affects_prediction_output": False,
        "prediction_output_modified": False,
        "prediction_json_modified": False,
        "score_modified": False,
        "rank_modified": False,
        "recommendation_modified": False,
        "expected_value_modified": False,
        "candidate_count": len(entries),
        "unique_racer_id_count": len(unique_racer_ids),
        "matched_candidate_count": matched,
        "missing_candidate_count": missing,
        "entries": entries,
    }

    write_json(OUTPUT_PATH, output)

    print("History feature shadow preview export: OK")
    print("STEP 141-A CHECK: OK")
    print(f"output={OUTPUT_PATH}")
    print(f"candidate_count={len(entries)}")
    print(f"matched_candidate_count={matched}")
    print(f"missing_candidate_count={missing}")


if __name__ == "__main__":
    main()
