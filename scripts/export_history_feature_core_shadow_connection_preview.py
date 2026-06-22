from pathlib import Path
import json
import hashlib
from datetime import datetime, timezone
import sys

CONFIG_PATH = Path("data/history_feature_config.json")
PREDICTION_PATH = Path("docs/prediction.json")
SHADOW_PREVIEW_PATH = Path("docs/prediction_history_feature_shadow_preview.json")
OUTPUT_PATH = Path("docs/prediction_history_feature_core_shadow_connection_preview.json")

STEP = "STEP146-A"
SCHEMA_VERSION = "history_feature_core_shadow_connection_preview.v1"


def fail(message):
    print(f"ERROR: {message}")
    sys.exit(1)


def load_json(path):
    if not path.exists():
        fail(f"missing file: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"invalid JSON: {path}: {exc}")


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_value(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def first_present(mapping, keys):
    if not isinstance(mapping, dict):
        return ""
    for key in keys:
        if key in mapping and mapping.get(key) not in (None, ""):
            return normalize_value(mapping.get(key))
    return ""


def make_candidate_key(item):
    if not isinstance(item, dict):
        return ""

    race_id = first_present(item, ["race_id", "raceId", "race_key", "raceKey"])
    race_no = first_present(item, ["race_no", "raceNo", "race_number", "raceNumber"])
    venue = first_present(item, ["venue_name", "venueName", "venue", "stadium", "place"])
    recommendation_id = first_present(item, ["recommendation_id", "recommendationId", "id"])
    candidate_id = first_present(item, ["candidate_id", "candidateId", "shadow_candidate_id", "adapter_candidate_id"])
    racer_id = first_present(item, ["racer_id", "racerId", "player_id", "playerId", "boat_number", "boatNo"])
    bet_type = first_present(item, ["bet_type", "betType", "type"])
    combination = first_present(item, ["combination", "selection", "ticket", "buy", "numbers"])

    parts = [
        race_id,
        race_no,
        venue,
        recommendation_id,
        candidate_id,
        racer_id,
        bet_type,
        combination,
    ]

    compact = [p for p in parts if p]
    if not compact:
        return ""

    return "|".join(compact)


def looks_like_prediction_candidate(item):
    if not isinstance(item, dict):
        return False

    keys = set(item.keys())
    candidate_keys = {
        "recommendation_id",
        "recommendationId",
        "race_id",
        "raceId",
        "race_no",
        "raceNo",
        "venue_name",
        "venueName",
        "bet_type",
        "betType",
        "combination",
        "selection",
        "score",
        "rank",
        "expected_value",
        "expectedValue",
        "expected_return",
        "odds",
    }

    return bool(keys & candidate_keys)


def looks_like_shadow_candidate(item):
    if not isinstance(item, dict):
        return False

    keys = set(item.keys())
    candidate_keys = {
        "candidate_id",
        "candidateId",
        "shadow_candidate_id",
        "adapter_candidate_id",
        "race_id",
        "raceId",
        "race_no",
        "raceNo",
        "racer_id",
        "racerId",
        "player_id",
        "playerId",
        "boat_number",
        "boatNo",
        "history_features",
        "history_feature",
        "features",
        "matched",
        "missing",
        "combination",
        "selection",
    }

    return bool(keys & candidate_keys)


def extract_prediction_candidates(data):
    candidates = []

    if isinstance(data, dict):
        races = data.get("races")
        if isinstance(races, list):
            for race_index, race in enumerate(races):
                if not isinstance(race, dict):
                    continue

                race_context = {
                    "race_id": race.get("race_id") or race.get("raceId") or f"race-{race_index + 1}",
                    "race_no": race.get("race_no") or race.get("raceNo") or race.get("race_number"),
                    "venue_name": race.get("venue_name") or race.get("venueName") or race.get("venue"),
                }

                recs = race.get("recommendations")
                if isinstance(recs, list):
                    for rec_index, rec in enumerate(recs):
                        if not isinstance(rec, dict):
                            continue
                        merged = dict(race_context)
                        merged.update(rec)
                        if "recommendation_id" not in merged:
                            merged["recommendation_id"] = rec.get("id") or f"{race_context['race_id']}-rec-{rec_index + 1}"
                        candidates.append(merged)

        recs = data.get("recommendations")
        if isinstance(recs, list):
            for rec_index, rec in enumerate(recs):
                if isinstance(rec, dict):
                    merged = dict(rec)
                    if "recommendation_id" not in merged:
                        merged["recommendation_id"] = rec.get("id") or f"top-rec-{rec_index + 1}"
                    candidates.append(merged)

    if not candidates:
        seen = set()

        def walk(obj):
            if isinstance(obj, dict):
                if looks_like_prediction_candidate(obj):
                    key = id(obj)
                    if key not in seen:
                        seen.add(key)
                        candidates.append(dict(obj))
                for value in obj.values():
                    walk(value)
            elif isinstance(obj, list):
                for value in obj:
                    walk(value)

        walk(data)

    normalized = []
    for index, item in enumerate(candidates):
        if not isinstance(item, dict):
            continue
        candidate = dict(item)
        candidate["_candidate_index"] = index
        candidate["_candidate_key"] = make_candidate_key(candidate) or f"prediction-candidate-{index + 1}"
        normalized.append(candidate)

    return normalized


def extract_shadow_candidates(data):
    candidates = []

    if isinstance(data, dict):
        preferred_keys = [
            "core_candidates",
            "connection_candidates",
            "shadow_candidates",
            "candidates",
            "entries",
            "items",
            "preview_entries",
            "results",
        ]

        for key in preferred_keys:
            value = data.get(key)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        candidates.append(dict(item))

    if not candidates:
        seen = set()

        def walk(obj):
            if isinstance(obj, dict):
                if looks_like_shadow_candidate(obj):
                    key = id(obj)
                    if key not in seen:
                        seen.add(key)
                        candidates.append(dict(obj))
                for value in obj.values():
                    walk(value)
            elif isinstance(obj, list):
                for value in obj:
                    walk(value)

        walk(data)

    normalized = []
    for index, item in enumerate(candidates):
        if not isinstance(item, dict):
            continue
        candidate = dict(item)
        candidate["_candidate_index"] = index
        candidate["_candidate_key"] = make_candidate_key(candidate) or f"shadow-candidate-{index + 1}"
        normalized.append(candidate)

    return normalized


def summarize_candidate(candidate):
    if not isinstance(candidate, dict):
        return {}

    keys = [
        "race_id",
        "raceId",
        "race_no",
        "raceNo",
        "venue_name",
        "venueName",
        "recommendation_id",
        "recommendationId",
        "candidate_id",
        "candidateId",
        "racer_id",
        "racerId",
        "player_id",
        "playerId",
        "boat_number",
        "boatNo",
        "bet_type",
        "betType",
        "combination",
        "selection",
        "_candidate_index",
        "_candidate_key",
    ]

    summary = {}
    for key in keys:
        if key in candidate:
            summary[key] = candidate.get(key)

    return summary


def build_connection_preview(prediction_data, shadow_data):
    prediction_candidates = extract_prediction_candidates(prediction_data)
    shadow_candidates = extract_shadow_candidates(shadow_data)

    shadow_by_key = {}
    for item in shadow_candidates:
        key = item.get("_candidate_key")
        if key:
            shadow_by_key.setdefault(key, []).append(item)

    matched = []
    missing = []

    for candidate in prediction_candidates:
        key = candidate.get("_candidate_key")
        shadow_matches = shadow_by_key.get(key, [])
        if shadow_matches:
            matched.append({
                "candidate": summarize_candidate(candidate),
                "shadow_match_count": len(shadow_matches),
                "shadow_matches": [summarize_candidate(x) for x in shadow_matches[:3]],
            })
        else:
            missing.append({
                "candidate": summarize_candidate(candidate),
                "reason": "no matching shadow candidate key found",
            })

    candidate_count = len(prediction_candidates)
    matched_candidate_count = len(matched)
    missing_candidate_count = len(missing)

    shadow_top_candidate_count = shadow_data.get("candidate_count") if isinstance(shadow_data, dict) else None
    shadow_top_matched_count = shadow_data.get("matched_candidate_count") if isinstance(shadow_data, dict) else None
    shadow_top_missing_count = shadow_data.get("missing_candidate_count") if isinstance(shadow_data, dict) else None

    return {
        "prediction_candidates": prediction_candidates,
        "shadow_candidates": shadow_candidates,
        "matched": matched,
        "missing": missing,
        "candidate_count": candidate_count,
        "matched_candidate_count": matched_candidate_count,
        "missing_candidate_count": missing_candidate_count,
        "shadow_preview_reported_candidate_count": shadow_top_candidate_count,
        "shadow_preview_reported_matched_candidate_count": shadow_top_matched_count,
        "shadow_preview_reported_missing_candidate_count": shadow_top_missing_count,
    }


def main():
    config = load_json(CONFIG_PATH)

    if config.get("enabled") is not False:
        fail("history feature config must remain enabled:false")

    if not PREDICTION_PATH.exists():
        fail(f"missing prediction file: {PREDICTION_PATH}")

    before_hash = sha256_file(PREDICTION_PATH)

    prediction_data = load_json(PREDICTION_PATH)
    shadow_data = load_json(SHADOW_PREVIEW_PATH)

    preview = build_connection_preview(prediction_data, shadow_data)

    after_read_hash = sha256_file(PREDICTION_PATH)
    if before_hash != after_read_hash:
        fail("docs/prediction.json changed during read phase")

    candidate_count = preview["candidate_count"]
    matched_candidate_count = preview["matched_candidate_count"]
    missing_candidate_count = preview["missing_candidate_count"]

    if matched_candidate_count + missing_candidate_count != candidate_count:
        fail("matched_candidate_count + missing_candidate_count must equal candidate_count")

    output = {
        "schema_version": SCHEMA_VERSION,
        "step": STEP,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "connection_mode": "shadow-only",
        "core_connection_enabled": False,
        "history_features_enabled": False,
        "affects_prediction_output": False,
        "prediction_json_unchanged": True,
        "prediction_core_modified": False,
        "score_changed": False,
        "rank_changed": False,
        "recommendation_changed": False,
        "expected_value_changed": False,
        "source_prediction_path": str(PREDICTION_PATH),
        "source_shadow_preview_path": str(SHADOW_PREVIEW_PATH),
        "output_path": str(OUTPUT_PATH),
        "prediction_json_sha256_before": before_hash,
        "prediction_json_sha256_after_read": after_read_hash,
        "candidate_count": candidate_count,
        "matched_candidate_count": matched_candidate_count,
        "missing_candidate_count": missing_candidate_count,
        "shadow_preview_reported_candidate_count": preview["shadow_preview_reported_candidate_count"],
        "shadow_preview_reported_matched_candidate_count": preview["shadow_preview_reported_matched_candidate_count"],
        "shadow_preview_reported_missing_candidate_count": preview["shadow_preview_reported_missing_candidate_count"],
        "connection_summary": {
            "prediction_candidate_count": len(preview["prediction_candidates"]),
            "shadow_candidate_count": len(preview["shadow_candidates"]),
            "matched_candidate_count": matched_candidate_count,
            "missing_candidate_count": missing_candidate_count,
            "match_method": "normalized diagnostic candidate key",
            "safe_mode": True,
            "writes_prediction_json": False,
            "writes_generated_outputs": False,
        },
        "matched_candidates_sample": preview["matched"][:20],
        "missing_candidates_sample": preview["missing"][:20],
        "safety_notes": [
            "This file is an isolated shadow connection preview.",
            "docs/prediction.json is read-only in this step.",
            "Prediction core is not modified.",
            "History feature config remains enabled:false.",
            "Prediction scores, ranks, recommendations, and expected values are unchanged.",
        ],
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    after_write_hash = sha256_file(PREDICTION_PATH)
    if before_hash != after_write_hash:
        fail("docs/prediction.json changed after writing preview output")

    print("History feature core shadow connection preview export: OK")
    print("STEP 146-A CHECK: OK")
    print(f"output={OUTPUT_PATH}")
    print(f"candidate_count={candidate_count}")
    print(f"matched_candidate_count={matched_candidate_count}")
    print(f"missing_candidate_count={missing_candidate_count}")
    print("connection_mode=shadow-only")


if __name__ == "__main__":
    main()
