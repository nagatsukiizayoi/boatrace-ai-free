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
    "docs/phase1_mvp_db_schema_implementation_plan_preview.json",
    "docs/phase1_mvp_db_schema_ddl_preview.json",
    "docs/phase1_mvp_db_schema_migration_script_preview.json",
    "scripts/check_phase1_mvp_db_schema_migration_draft.py",
    "scripts/migrate_phase1_mvp_db_schema.py",
    "scripts/check_phase1_mvp_db_schema_migration_execution_preview.py",
    "docs/phase1_mvp_db_schema_migration_execution_preview.json",
    "scripts/check_phase1_mvp_db_schema_runtime_guard_preview.py",
    "docs/phase1_mvp_db_schema_runtime_guard_preview.json",
    "scripts/check_phase1_mvp_db_schema_explicit_execution_gate_preview.py",
    "docs/phase1_mvp_db_schema_explicit_execution_gate_preview.json",
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
    "scripts/check_phase1_mvp_db_schema_implementation_plan_preview.py",
    "scripts/check_phase1_mvp_db_schema_ddl_preview.py",
    "scripts/check_phase1_mvp_db_schema_migration_script_preview.py",
    "scripts/check_phase1_mvp_db_schema_migration_draft.py",
    "scripts/check_phase1_mvp_db_schema_migration_execution_preview.py",
    "scripts/check_phase1_mvp_db_schema_runtime_guard_preview.py",
    "scripts/check_phase1_mvp_db_schema_explicit_execution_gate_preview.py",
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

    print("=== STEP 158-C final design compatibility preview readiness check ===")
    _step158c_proc = __import__("subprocess").run(
        [__import__("sys").executable, "scripts/check_phase1_mvp_db_schema_final_design_compatibility_preview.py"],
        text=True,
        stdout=__import__("subprocess").PIPE,
        stderr=__import__("subprocess").STDOUT,
    )
    print(_step158c_proc.stdout, end="")
    if _step158c_proc.returncode != 0:
        raise SystemExit("ERROR: STEP 158-C checker failed in readiness")
    if "STEP 158-C CHECK: OK" not in _step158c_proc.stdout:
        raise SystemExit("ERROR: missing STEP 158-C CHECK: OK in readiness")
    if "Phase 1 MVP DB schema final design compatibility preview validation: OK" not in _step158c_proc.stdout:
        raise SystemExit("ERROR: missing final design compatibility validation OK in readiness")
    print("Dashboard readiness outputs validation: OK")
    print("STEP 85 CHECK: OK")


if __name__ == "__main__":
    main()
