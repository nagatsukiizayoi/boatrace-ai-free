from pathlib import Path
import json
import subprocess
import sys

REQUIRED_FILES = [
    "docs/index.html",
    "docs/healthcheck.html",
    "docs/prediction.json",
    "README.md",
    "scripts/ensure_prediction_json_dashboard_compat.py",
    "scripts/check_recommendation_reasons.py",
    "scripts/check_dashboard_final_readiness.py",
    "scripts/check_readme_dashboard_readiness_doc.py",
    "scripts/check_readme_dashboard_readiness_badge.py",
    "scripts/check_dashboard_readiness_workflows.py",
    "scripts/check_dashboard_readiness_runbook.py",
    ".github/workflows/check-dashboard-final-readiness.yml",
    "docs/prediction_history_feature_shadow_preview.json",
    "scripts/check_history_feature_shadow_preview.py",
    "docs/prediction_history_feature_core_shadow_connection_preview.json",
    "docs/prediction_history_feature_key_normalization_preview.json",
    "docs/phase1_mvp_db_schema_preview.json",
]

CHECK_SCRIPTS = [
        "scripts/check_dashboard_history_feature_adapter_preview.py",
    "scripts/ensure_prediction_json_dashboard_compat.py",
    "scripts/check_recommendation_reasons.py",
    "scripts/check_dashboard_final_readiness.py",
    "scripts/check_readme_dashboard_readiness_doc.py",
    "scripts/check_readme_dashboard_readiness_badge.py",
    "scripts/check_history_feature_shadow_preview.py",
    "scripts/check_dashboard_history_feature_shadow_preview.py",
    "scripts/check_history_feature_core_shadow_connection_preview.py",
    "scripts/check_history_feature_key_normalization_preview.py",
    "scripts/check_phase1_mvp_db_schema_preview.py",
]


def fail(message):
    print(f"ERROR: {message}")
    sys.exit(1)


def run(cmd):
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, text=True)
    if result.returncode != 0:
        fail(f"command failed: {' '.join(cmd)}")


def load_prediction_json():
    try:
        return json.loads(Path("docs/prediction.json").read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"docs/prediction.json is not valid JSON: {exc}")


def main():
    for path in REQUIRED_FILES:
        if not Path(path).exists():
            fail(f"required file does not exist: {path}")

    for script in CHECK_SCRIPTS:
        run(["python", "-m", "py_compile", script])

    # Important:
    # prediction.json may be generated in a minimal format.
    # Normalize it before checking dashboard-required keys.
    run(["python", "scripts/ensure_prediction_json_dashboard_compat.py"])
    run(["python", "-m", "json.tool", "docs/prediction.json"])

    data = load_prediction_json()

    if not isinstance(data, dict):
        fail("docs/prediction.json top-level must be an object")

    required_prediction_keys = [
        "run_key",
        "model_name",
        "model_version",
        "target_date",
        "summary",
        "races",
        "alerts",
        "recommendation_reasoning",
        "explainability",
    ]

    missing = [key for key in required_prediction_keys if key not in data]
    if missing:
        fail(f"docs/prediction.json missing keys after compatibility patch: {missing}")

    races = data.get("races")
    if not isinstance(races, list) or not races:
        fail("docs/prediction.json races must be a non-empty list")

    recommendations = data.get("recommendations")
    if not isinstance(recommendations, list) or not recommendations:
        fail("docs/prediction.json recommendations must be a non-empty list")

    run(["python", "scripts/check_recommendation_reasons.py"])
    run(["python", "scripts/check_dashboard_final_readiness.py"])
    run(["python", "scripts/check_readme_dashboard_readiness_doc.py"])
    run(["python", "scripts/check_readme_dashboard_readiness_badge.py"])
    run(["python", "scripts/check_dashboard_readiness_workflows.py"])
    run(["python", "scripts/check_dashboard_readiness_runbook.py"])

    print("Dashboard readiness outputs validation: OK")
    print("STEP 85 CHECK: OK")


if __name__ == "__main__":
    main()
