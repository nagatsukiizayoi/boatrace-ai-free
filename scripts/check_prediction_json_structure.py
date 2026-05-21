import json
from pathlib import Path

JSON_PATH = Path("docs/prediction.json")


def fail(errors):
    print("Prediction JSON structure validation errors:")
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
        "races",
        "predictions",
        "tickets",
        "recommendations",
        "summary",
    }

    if not (keys & expected_any_keys):
        errors.append(
            "prediction.json does not contain expected top-level keys. "
            f"found keys: {sorted(keys)}"
        )

    list_keys = [
        "races",
        "predictions",
        "tickets",
        "recommendations",
    ]

    found_prediction_lists = []

    for key in list_keys:
        if key in data:
            if not isinstance(data[key], list):
                errors.append(f"{key} must be a list")
            else:
                found_prediction_lists.append((key, len(data[key])))

    if found_prediction_lists:
        if all(count == 0 for _, count in found_prediction_lists):
            errors.append(
                "all prediction-related lists are empty: "
                f"{found_prediction_lists}"
            )
    else:
        if "summary" not in data:
            errors.append(
                "no prediction-related list found. "
                "expected one of races, predictions, tickets, recommendations, or summary"
            )

    if "summary" in data and not isinstance(data["summary"], dict):
        errors.append("summary must be an object")

    if errors:
        fail(errors)

    print("Prediction JSON structure validation: OK")
    print("STEP 66 CHECK: OK")


if __name__ == "__main__":
    main()
