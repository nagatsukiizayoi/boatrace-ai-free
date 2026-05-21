from pathlib import Path

README_PATH = Path("README.md")
WORKFLOW_PATH = Path(".github/workflows/make_prediction.yml")

BADGE_TOKEN = "https://github.com/nagatsukiizayoi/boatrace-ai-free/actions/workflows/make_prediction.yml/badge.svg"
BADGE_LABEL = "![make_prediction]"


def fail(errors):
    print("README make_prediction badge validation errors:")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)


def main():
    errors = []

    if not README_PATH.exists():
        errors.append(f"missing file: {README_PATH}")

    if not WORKFLOW_PATH.exists():
        errors.append(f"missing workflow file: {WORKFLOW_PATH}")

    if errors:
        fail(errors)

    text = README_PATH.read_text(encoding="utf-8")

    required_tokens = [
        BADGE_LABEL,
        BADGE_TOKEN,
        "make_prediction workflow",
        "STEP71_MAKE_PREDICTION_WORKFLOW_DOC",
        "STEP71_END",
    ]

    for token in required_tokens:
        if token not in text:
            errors.append(f"missing README token: {token}")

    if "<<<<<<<" in text or "=======" in text or ">>>>>>>" in text:
        errors.append("README contains Git conflict markers")

    if errors:
        fail(errors)

    print("README make_prediction badge validation: OK")
    print("STEP 73 CHECK: OK")


if __name__ == "__main__":
    main()
