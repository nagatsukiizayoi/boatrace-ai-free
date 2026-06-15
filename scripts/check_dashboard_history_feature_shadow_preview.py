from pathlib import Path
import json
import re
import sys

INDEX_PATH = Path("docs/index.html")
JSON_PATH = Path("docs/prediction_history_feature_shadow_preview.json")
CONFIG_PATH = Path("data/history_feature_config.json")
PREDICTION_PATH = Path("docs/prediction.json")

REQUIRED_HTML_MARKERS = [
    "history-feature-shadow-preview-section",
    "prediction_history_feature_shadow_preview.json",
    "loadHistoryFeatureShadowPreview",
    "history-feature-shadow-candidate-count",
    "history-feature-shadow-matched-count",
    "history-feature-shadow-missing-count",
    "history-feature-shadow-enabled",
    "history-feature-shadow-affects-output",
    "history-feature-shadow-prediction-json-unchanged",
    "history-feature-shadow-preview-only",
]

REQUIRED_JSON_KEYS = [
    "schema_version",
    "step",
    "history_features_enabled",
    "affects_prediction_output",
    "candidate_count",
    "matched_candidate_count",
    "missing_candidate_count",
]

def fail(message):
    print(f"ERROR: {message}")
    sys.exit(1)

def load_json(path):
    if not path.exists():
        fail(f"missing JSON file: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"invalid JSON {path}: {exc}")

def main():
    if not INDEX_PATH.exists():
        fail(f"missing dashboard HTML: {INDEX_PATH}")

    html = INDEX_PATH.read_text(encoding="utf-8")

    for marker in REQUIRED_HTML_MARKERS:
        if marker not in html:
            fail(f"missing dashboard marker: {marker}")

    data = load_json(JSON_PATH)
    config = load_json(CONFIG_PATH)

    for key in REQUIRED_JSON_KEYS:
        if key not in data:
            fail(f"missing shadow preview key: {key}")

    if config.get("enabled") is not False:
        fail("history feature config must remain enabled:false")

    false_flags = [
        "history_features_enabled",
        "affects_prediction_output",
    ]
    for key in false_flags:
        if data.get(key) is not False:
            fail(f"{key} must be false")

    true_flags = [
            ]
    for key in true_flags:
        if data.get(key) is not True:
            fail(f"{key} must be true")

    if "prediction_json_unchanged" in data and data.get("prediction_json_unchanged") is not True:
        fail("prediction_json_unchanged must be true when present")

    for key in ["prediction_json_unchanged", "shadow_preview_only"]:
        if key in data and data.get(key) is not True:
            fail(f"{key} must be true when present")

    for key in ["candidate_count", "matched_candidate_count", "missing_candidate_count"]:
        value = data.get(key)
        if not isinstance(value, int) or value < 0:
            fail(f"{key} must be a non-negative integer")

    if data["matched_candidate_count"] + data["missing_candidate_count"] != data["candidate_count"]:
        fail("matched_candidate_count + missing_candidate_count must equal candidate_count")

    if not PREDICTION_PATH.exists():
        fail("docs/prediction.json is missing")

    print("Dashboard history feature shadow preview validation: OK")
    print("STEP 141-E CHECK: OK")
    print(f"candidate_count={data.get('candidate_count')}")
    print(f"matched_candidate_count={data.get('matched_candidate_count')}")
    print(f"missing_candidate_count={data.get('missing_candidate_count')}")

if __name__ == "__main__":
    main()
