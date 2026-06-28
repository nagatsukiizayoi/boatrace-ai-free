from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any


CONFIG_PATH = Path("data/history_feature_config.json")
PREDICTION_PATH = Path("docs/prediction.json")
CORE_PREVIEW_PATH = Path("docs/prediction_history_feature_core_shadow_connection_preview.json")
OUTPUT_PATH = Path("docs/prediction_history_feature_key_normalization_preview.json")


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


def normalize_candidate_key(value: Any) -> str:
    """
    Candidate key normalization preview only.

    This function does not change prediction output.
    It only previews whether key format differences may explain
    matched_candidate_count=0.
    """
    if value is None:
        return ""

    text = str(value)
    text = unicodedata.normalize("NFKC", text)
    text = text.strip().lower()

    # Remove common separators and whitespace.
    text = re.sub(r"[\s_\-:/|]+", "", text)

    # Keep only simple comparable characters.
    text = re.sub(r"[^0-9a-zぁ-んァ-ン一-龥]", "", text)

    return text


def extract_candidate_key_from_item(item: Any) -> str | None:
    if isinstance(item, str):
        return item

    if isinstance(item, int):
        return str(item)

    if not isinstance(item, dict):
        return None

    candidate_fields = [
        "candidate_key",
        "key",
        "id",
        "race_key",
        "entry_key",
        "prediction_candidate_key",
        "shadow_candidate_key",
        "normalized_key",
    ]

    for field in candidate_fields:
        if field in item and item[field] not in (None, ""):
            return str(item[field])

    # Fallback: combine common race/boat fields if present.
    race_like = None
    boat_like = None

    for field in ["race_id", "race", "race_no", "race_number"]:
        if field in item and item[field] not in (None, ""):
            race_like = str(item[field])
            break

    for field in ["boat", "boat_no", "boat_number", "teiban", "枠番"]:
        if field in item and item[field] not in (None, ""):
            boat_like = str(item[field])
            break

    if race_like is not None and boat_like is not None:
        return f"{race_like}-{boat_like}"

    return None


def collect_keys_from_named_lists(data: Any, names: list[str]) -> list[str]:
    keys: list[str] = []

    if not isinstance(data, dict):
        return keys

    for name in names:
        value = data.get(name)
        if isinstance(value, list):
            for item in value:
                key = extract_candidate_key_from_item(item)
                if key:
                    keys.append(key)

    return keys


def collect_keys_recursively(data: Any, limit: int = 200) -> list[str]:
    keys: list[str] = []

    interesting_fields = {
        "candidate_key",
        "key",
        "race_key",
        "entry_key",
        "prediction_candidate_key",
        "shadow_candidate_key",
    }

    def walk(obj: Any) -> None:
        if len(keys) >= limit:
            return

        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in interesting_fields and v not in (None, ""):
                    keys.append(str(v))
                    if len(keys) >= limit:
                        return
                walk(v)

        elif isinstance(obj, list):
            for item in obj:
                walk(item)
                if len(keys) >= limit:
                    return

    walk(data)
    return keys


def unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []

    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)

    return out


def main() -> None:
    config = load_json(CONFIG_PATH)
    prediction = load_json(PREDICTION_PATH)
    core_preview = load_json(CORE_PREVIEW_PATH)

    if config.get("enabled") is not False:
        fail(f"history feature config must remain enabled:false, got {config.get('enabled')!r}")

    if core_preview.get("connection_mode") != "shadow-only":
        fail(f"core preview connection_mode must be shadow-only, got {core_preview.get('connection_mode')!r}")

    if core_preview.get("core_connection_enabled") is not False:
        fail("core preview core_connection_enabled must be false")

    if core_preview.get("affects_prediction_output") is not False:
        fail("core preview affects_prediction_output must be false")

    if core_preview.get("history_features_enabled") is not False:
        fail("core preview history_features_enabled must be false")

    prediction_keys = collect_keys_from_named_lists(
        core_preview,
        [
            "prediction_candidates",
            "prediction_candidate_keys",
            "candidates",
            "missing_candidates",
        ],
    )

    shadow_keys = collect_keys_from_named_lists(
        core_preview,
        [
            "shadow_candidates",
            "shadow_candidate_keys",
            "history_candidates",
            "matched_candidates",
        ],
    )

    if not prediction_keys:
        prediction_keys = collect_keys_recursively(prediction)

    if not shadow_keys:
        shadow_keys = collect_keys_from_named_lists(
            core_preview,
            [
                "shadow_preview_candidates",
                "history_feature_candidates",
                "history_candidates",
            ],
        )

    prediction_keys = unique_preserve_order(prediction_keys)
    shadow_keys = unique_preserve_order(shadow_keys)

    normalized_prediction = {
        key: normalize_candidate_key(key)
        for key in prediction_keys
    }

    normalized_shadow = {
        key: normalize_candidate_key(key)
        for key in shadow_keys
    }

    prediction_normalized_set = {
        value for value in normalized_prediction.values()
        if value
    }

    shadow_normalized_set = {
        value for value in normalized_shadow.values()
        if value
    }

    matched_normalized_keys = sorted(prediction_normalized_set & shadow_normalized_set)

    normalization_samples = []

    for original_key, normalized_key in list(normalized_prediction.items())[:50]:
        normalization_samples.append(
            {
                "source": "prediction",
                "original_candidate_key": original_key,
                "normalized_candidate_key": normalized_key,
                "match_after_normalization": normalized_key in shadow_normalized_set,
            }
        )

    for original_key, normalized_key in list(normalized_shadow.items())[:50]:
        normalization_samples.append(
            {
                "source": "shadow",
                "original_candidate_key": original_key,
                "normalized_candidate_key": normalized_key,
                "match_after_normalization": normalized_key in prediction_normalized_set,
            }
        )

    result = {
        "step": "STEP148-A",
        "preview_type": "candidate-key-normalization",
        "connection_mode": "shadow-only",
        "safe_mode": True,
        "config_enabled": False,
        "core_connection_enabled": False,
        "affects_prediction_output": False,
        "writes_prediction_json": False,
        "history_features_enabled": False,
        "prediction_core_connected": False,
        "source_files": {
            "config": str(CONFIG_PATH),
            "prediction": str(PREDICTION_PATH),
            "core_shadow_connection_preview": str(CORE_PREVIEW_PATH),
        },
        "output_file": str(OUTPUT_PATH),
        "original_core_shadow_preview_counts": {
            "candidate_count": core_preview.get("candidate_count"),
            "prediction_candidate_count": core_preview.get("prediction_candidate_count"),
            "shadow_candidate_count": core_preview.get("shadow_candidate_count"),
            "matched_candidate_count": core_preview.get("matched_candidate_count"),
            "missing_candidate_count": core_preview.get("missing_candidate_count"),
        },
        "normalization_rules": [
            "NFKC unicode normalization",
            "strip leading and trailing whitespace",
            "lowercase ASCII letters",
            "remove whitespace, underscore, hyphen, colon, slash, and pipe separators",
            "keep only digits, ASCII letters, kana, and common CJK characters",
        ],
        "normalization_preview_counts": {
            "prediction_key_count": len(prediction_keys),
            "shadow_key_count": len(shadow_keys),
            "matched_after_normalization_count": len(matched_normalized_keys),
        },
        "matched_normalized_keys_sample": matched_normalized_keys[:50],
        "normalization_samples": normalization_samples,
        "decision": {
            "matched_candidate_count_zero_is_allowed_in_shadow_only_preview": True,
            "do_not_enable_history_features": True,
            "do_not_connect_prediction_core": True,
            "do_not_modify_prediction_json": True,
            "next_step": "STEP148-B will add a checker for this key normalization preview.",
        },
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("History feature key normalization preview export: OK")
    print("STEP 148-A CHECK: OK")
    print(f"output={OUTPUT_PATH}")
    print("connection_mode=shadow-only")
    print("core_connection_enabled=False")
    print("affects_prediction_output=False")
    print("writes_prediction_json=False")
    print("history_features_enabled=False")
    print(f"prediction_key_count={len(prediction_keys)}")
    print(f"shadow_key_count={len(shadow_keys)}")
    print(f"matched_after_normalization_count={len(matched_normalized_keys)}")


if __name__ == "__main__":
    main()
