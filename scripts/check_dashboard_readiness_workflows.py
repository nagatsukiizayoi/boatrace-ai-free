from pathlib import Path
import sys

WORKFLOW_FILES = [
    Path(".github/workflows/check-dashboard-final-readiness.yml"),
    Path(".github/workflows/check-integrated-schema.yml"),
    Path(".github/workflows/check-csv-prediction-json.yml"),
    Path(".github/workflows/check-dashboard-quality-score-cards.yml"),
]

REQUIRED_TOKENS = [
    "actions/checkout",
    "actions/setup-python",
    "ensure_prediction_json_dashboard_compat.py",
    "check_recommendation_reasons.py",
    "check_dashboard_final_readiness.py",
    "check_readme_dashboard_readiness_doc.py",
    "check_readme_dashboard_readiness_badge.py",
    "check_dashboard_readiness_outputs_ready.py",
]

CONFLICT_MARKERS = [
    "<<<<<<<",
    "=======",
    ">>>>>>>",
]


def main():
    errors = []
    combined = ""

    for path in WORKFLOW_FILES:
        if not path.exists():
            errors.append(f"workflow file does not exist: {path}")
            continue

        text = path.read_text(encoding="utf-8")
        combined += "\n" + text

        for marker in CONFLICT_MARKERS:
            if marker in text:
                errors.append(f"{path} contains Git conflict marker: {marker}")

        if "\t" in text:
            errors.append(f"{path} contains tab characters")

    for token in REQUIRED_TOKENS:
        if token not in combined:
            errors.append(f"missing workflow token: {token}")

    if errors:
        print("Dashboard readiness workflows validation failed")
        for error in errors:
            print(f"ERROR: {error}")
        sys.exit(1)

    print("Dashboard readiness workflows validation: OK")
    print("STEP 87 CHECK: OK")


if __name__ == "__main__":
    main()
