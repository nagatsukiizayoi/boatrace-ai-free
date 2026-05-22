from pathlib import Path
import sys

README = Path("README.md")
WORKFLOW = Path(".github/workflows/check-dashboard-final-readiness.yml")

REQUIRED_TOKENS = [
    "![Dashboard readiness]",
    "check-dashboard-final-readiness.yml/badge.svg",
    "Dashboard readiness and prediction JSON compatibility",
    "STEP82_DASHBOARD_READINESS_DOC",
    "STEP82_END",
]

CONFLICT_MARKERS = [
    "<<<<<<<",
    "=======",
    ">>>>>>>",
]


def main():
    errors = []

    if not README.exists():
        errors.append("README.md does not exist")
    else:
        text = README.read_text(encoding="utf-8")

        for token in REQUIRED_TOKENS:
            if token not in text:
                errors.append(f"missing README token: {token}")

        for marker in CONFLICT_MARKERS:
            if marker in text:
                errors.append(f"README contains Git conflict marker: {marker}")

    if not WORKFLOW.exists():
        errors.append(f"workflow file does not exist: {WORKFLOW}")

    if errors:
        print("README dashboard readiness badge validation failed")
        for error in errors:
            print(f"ERROR: {error}")
        sys.exit(1)

    print("README dashboard readiness badge validation: OK")
    print("STEP 84 CHECK: OK")


if __name__ == "__main__":
    main()
