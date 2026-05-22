from pathlib import Path

WORKFLOW_PATH = Path(".github/workflows/make_prediction.yml")


def fail(errors):
    print("make_prediction schedule validation errors:")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)


def main():
    errors = []

    if not WORKFLOW_PATH.exists():
        fail([f"missing workflow: {WORKFLOW_PATH}"])

    text = WORKFLOW_PATH.read_text(encoding="utf-8")

    required_tokens = [
        "on:",
        "workflow_dispatch",
        "schedule:",
        "cron:",
        "0 12 * * *",
    ]

    for token in required_tokens:
        if token not in text:
            errors.append(f"missing workflow token: {token}")

    if "<<<<<<<" in text or "=======" in text or ">>>>>>>" in text:
        errors.append("workflow contains Git conflict markers")

    if "\t" in text:
        errors.append("workflow contains tab characters")

    if errors:
        fail(errors)

    print("make_prediction schedule validation: OK")
    print("STEP 75 CHECK: OK")


if __name__ == "__main__":
    main()
