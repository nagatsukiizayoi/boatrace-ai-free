from pathlib import Path

WORKFLOW_PATH = Path(".github/workflows/make_prediction.yml")


def fail(errors):
    print("Make prediction workflow validation errors:")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)


def main():
    errors = []

    if not WORKFLOW_PATH.exists():
        fail([f"missing workflow file: {WORKFLOW_PATH}"])

    text = WORKFLOW_PATH.read_text(encoding="utf-8")

    required_tokens = [
        "name:",
        "on:",
        "jobs:",
        "runs-on:",
        "actions/checkout",
        "actions/setup-python",
        "python-version",
        "build_database.py",
        "run_full_prediction_pipeline.py",
        "prediction.json",
        "json.tool",
        "check_prediction_json_structure.py",
        "check_prediction_run_summary_structure.py",
        "check_prediction_outputs_consistency.py",
        "0 12 * * *",
        "cron:",
        "schedule:",
        "workflow_dispatch",
        "check_make_prediction_schedule.py",
        "check_readme_make_prediction_badge.py",
        "check_readme_make_prediction_doc.py",
        "check_make_prediction_outputs_ready.py",
    ]

    for token in required_tokens:
        if token not in text:
            errors.append(f"missing required token in workflow: {token}")

    # STEP66/67/68 のチェック名またはスクリプトが含まれているか確認
    step_checks = {
        "STEP66 prediction.json structure": "check_prediction_json_structure.py",
        "STEP67 prediction_run_summary structure": "check_prediction_run_summary_structure.py",
        "STEP68 prediction outputs consistency": "check_prediction_outputs_consistency.py",
    }

    for label, token in step_checks.items():
        if token not in text:
            errors.append(f"missing {label}: {token}")

    # YAMLとして最低限まずそうなパターンを検出
    if "\t" in text:
        errors.append("workflow contains tab characters; use spaces for YAML indentation")

    if "<<<<<<<" in text or "=======" in text or ">>>>>>>" in text:
        errors.append("workflow contains Git conflict markers")

    if errors:
        fail(errors)

    print("Make prediction workflow validation: OK")
    print("STEP 69 CHECK: OK")


if __name__ == "__main__":
    main()
