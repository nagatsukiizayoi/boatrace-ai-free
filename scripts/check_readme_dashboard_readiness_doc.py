from pathlib import Path
import sys

README = Path("README.md")

REQUIRED_TOKENS = [
    "STEP82_DASHBOARD_READINESS_DOC",
    "STEP82_END",
    "Dashboard readiness and prediction JSON compatibility",
    "docs/index.html",
    "docs/healthcheck.html",
    "docs/prediction.json",
    "scripts/ensure_prediction_json_dashboard_compat.py",
    "scripts/check_recommendation_reasons.py",
    "scripts/check_dashboard_final_readiness.py",
    "expected_value",
    "value_grade",
    "reason_version",
    "recommendation_reason",
    "reason_points",
    "risk_note",
    "recommendation_reasoning.version",
    "STEP 80 CHECK: OK",
    "STEP 100 CHECK: OK",
    "STEP 85 CHECK: OK",
    "Dashboard readiness outputs validation: OK",
    "scripts/check_dashboard_readiness_outputs_ready.py",
    "STEP86_END",
    "STEP86_DASHBOARD_READINESS_INTEGRATED_DOC",
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

    if errors:
        print("README dashboard readiness documentation validation failed")
        for error in errors:
            print(f"ERROR: {error}")
        sys.exit(1)

    print("README dashboard readiness documentation validation: OK")
    print("STEP 83 CHECK: OK")


if __name__ == "__main__":
    main()
