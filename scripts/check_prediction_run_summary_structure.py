import json
from pathlib import Path

JSON_PATH = Path("docs/prediction_run_summary.json")


def fail(errors):
    print("Prediction run summary validation errors:")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)


def main():
    errors = []

    if not JSON_PATH.exists():
        fail([f"missing file: {JSON_PATH}"])

    try:
        data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        fail([f"invalid JSON: {exc}"])

    if not isinstance(data, dict):
        fail(["top-level JSON must be an object"])

    keys = set(data.keys())

    expected_any_keys = {
        "generated_at",
        "updated_at",
        "run_key",
        "target_date",
        "model",
        "status",
        "summary",
        "race_count",
        "ticket_count",
        "recommendation_count",
        "total_amount",
        "alerts",
        "quality",
        "quality_score",
    }

    if not (keys & expected_any_keys):
        errors.append(
            "prediction_run_summary.json does not contain expected keys. "
            f"found keys: {sorted(keys)}"
        )

    if "summary" in data and not isinstance(data["summary"], dict):
        errors.append("summary must be an object if present")

    numeric_candidates = [
        "race_count",
        "ticket_count",
        "recommendation_count",
        "total_amount",
        "quality_score",
    ]

    for key in numeric_candidates:
        if key in data:
            if not isinstance(data[key], (int, float)):
                errors.append(f"{key} must be numeric")
            elif data[key] < 0:
                errors.append(f"{key} must be non-negative")

    if "alerts" in data and not isinstance(data["alerts"], (list, dict)):
        errors.append("alerts must be a list or object if present")

    # 空オブジェクトは不可
    if not data:
        errors.append("prediction_run_summary.json is empty")

    if errors:
        fail(errors)

    print("Prediction run summary structure validation: OK")
    print("STEP 67 CHECK: OK")


if __name__ == "__main__":
    main()
