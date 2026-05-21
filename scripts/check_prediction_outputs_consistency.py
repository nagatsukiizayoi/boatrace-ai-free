import json
from pathlib import Path

PREDICTION_PATH = Path("docs/prediction.json")
SUMMARY_PATH = Path("docs/prediction_run_summary.json")


def fail(errors):
    print("Prediction outputs consistency validation errors:")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)


def load_json(path):
    if not path.exists():
        fail([f"missing file: {path}"])
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail([f"invalid JSON in {path}: {exc}"])


def get_first_existing(data, keys):
    for key in keys:
        if isinstance(data, dict) and key in data:
            return data[key]
    return None


def count_list(data, keys):
    for key in keys:
        value = get_first_existing(data, [key])
        if isinstance(value, list):
            return len(value)
    return None


def main():
    errors = []

    prediction = load_json(PREDICTION_PATH)
    summary = load_json(SUMMARY_PATH)

    if not isinstance(prediction, dict):
        fail(["prediction.json top-level must be an object"])

    if not isinstance(summary, dict):
        fail(["prediction_run_summary.json top-level must be an object"])

    # run_key の整合性
    prediction_run_key = get_first_existing(prediction, ["run_key", "prediction_run_key"])
    summary_run_key = get_first_existing(summary, ["run_key", "prediction_run_key"])

    if prediction_run_key is not None and summary_run_key is not None:
        if str(prediction_run_key) != str(summary_run_key):
            errors.append(
                f"run_key mismatch: prediction={prediction_run_key}, summary={summary_run_key}"
            )

    # target_date の整合性
    prediction_target_date = get_first_existing(prediction, ["target_date", "date"])
    summary_target_date = get_first_existing(summary, ["target_date", "date"])

    if prediction_target_date is not None and summary_target_date is not None:
        if str(prediction_target_date) != str(summary_target_date):
            errors.append(
                f"target_date mismatch: prediction={prediction_target_date}, summary={summary_target_date}"
            )

    # model の整合性
    prediction_model = get_first_existing(prediction, ["model", "model_name"])
    summary_model = get_first_existing(summary, ["model", "model_name"])

    if prediction_model is not None and summary_model is not None:
        if str(prediction_model) != str(summary_model):
            errors.append(
                f"model mismatch: prediction={prediction_model}, summary={summary_model}"
            )

    # recommendations 件数の整合性
    prediction_recommendation_count = count_list(
        prediction,
        ["recommendations", "tickets", "predictions"]
    )

    summary_recommendation_count = get_first_existing(
        summary,
        ["recommendation_count", "ticket_count", "prediction_count"]
    )

    if prediction_recommendation_count is not None and summary_recommendation_count is not None:
        if isinstance(summary_recommendation_count, (int, float)):
            if int(summary_recommendation_count) < 0:
                errors.append("summary recommendation count must be non-negative")
            elif prediction_recommendation_count != int(summary_recommendation_count):
                errors.append(
                    "recommendation count mismatch: "
                    f"prediction list count={prediction_recommendation_count}, "
                    f"summary count={summary_recommendation_count}"
                )
        else:
            errors.append("summary recommendation count must be numeric")

    # races 件数の整合性
    prediction_race_count = count_list(prediction, ["races"])
    summary_race_count = get_first_existing(summary, ["race_count", "races_count"])

    if prediction_race_count is not None and summary_race_count is not None:
        if isinstance(summary_race_count, (int, float)):
            if int(summary_race_count) < 0:
                errors.append("summary race_count must be non-negative")
            elif prediction_race_count != int(summary_race_count):
                errors.append(
                    f"race_count mismatch: prediction races={prediction_race_count}, "
                    f"summary race_count={summary_race_count}"
                )
        else:
            errors.append("summary race_count must be numeric")

    # generated_at / updated_at の存在確認
    prediction_timestamp = get_first_existing(prediction, ["generated_at", "updated_at"])
    summary_timestamp = get_first_existing(summary, ["generated_at", "updated_at"])

    if prediction_timestamp is None:
        errors.append("prediction.json missing generated_at or updated_at")

    if summary_timestamp is None:
        errors.append("prediction_run_summary.json missing generated_at or updated_at")

    # どちらも空すぎないか
    if not prediction:
        errors.append("prediction.json is empty")

    if not summary:
        errors.append("prediction_run_summary.json is empty")

    if errors:
        fail(errors)

    print("Prediction outputs consistency validation: OK")
    print("STEP 68 CHECK: OK")


if __name__ == "__main__":
    main()
