from pathlib import Path

README_PATH = Path("README.md")


def fail(errors):
    print("README make_prediction documentation validation errors:")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)


def main():
    errors = []

    if not README_PATH.exists():
        fail([f"missing file: {README_PATH}"])

    text = README_PATH.read_text(encoding="utf-8")

    required_tokens = [
        "STEP71_MAKE_PREDICTION_WORKFLOW_DOC",
        "STEP71_END",
        "make_prediction workflow",
        "docs/prediction.json",
        "docs/prediction_run_summary.json",
        ".github/workflows/make_prediction.yml",
        "check_prediction_json_structure.py",
        "check_prediction_run_summary_structure.py",
        "check_prediction_outputs_consistency.py",
        "check_make_prediction_workflow.py",
        "check_make_prediction_outputs_ready.py",
        "STEP 66 CHECK: OK",
        "STEP 70 CHECK: OK",
        "workflow_dispatch",
        "21:00 JST",
        "0 12 * * *",
        "STEP77_END",
        "STEP77_MAKE_PREDICTION_SCHEDULE_DOC",
    ]

    for token in required_tokens:
        if token not in text:
            errors.append(f"missing README token: {token}")

    if "=======" in text or "<<<<<<<" in text or ">>>>>>>" in text:
        errors.append("README contains Git conflict markers")

    if errors:
        fail(errors)

    print("README make_prediction documentation validation: OK")
    print("STEP 72 CHECK: OK")


if __name__ == "__main__":
    main()
