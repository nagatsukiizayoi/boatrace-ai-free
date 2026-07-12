#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

CHECKS = [
    ["python", "scripts/check_history_sources_config.py"],
    ["python", "scripts/check_google_sheets_history_profile.py"],
    ["python", "scripts/check_google_sheets_column_mapping.py"],
    ["python", "scripts/check_history_results_csv.py"],
    ["python", "scripts/check_history_database.py"],
    ["python", "scripts/check_history_database_summary.py"],
    ["python", "scripts/check_racer_history_features.py"],
    ["python", "scripts/check_racer_history_features_summary.py"],
    ["python", "scripts/check_history_feature_config.py"],
    ["python", "scripts/check_history_feature_loader.py"],
    ["python", "scripts/check_prediction_history_feature_join.py"],
    ["python", "scripts/check_prediction_history_feature_preview.py"],
    ["python", "scripts/check_history_feature_ab_preview_schema.py"],
    ["python", "scripts/check_history_feature_ab_preview.py"],
    ["python", "scripts/check_dashboard_history_feature_summary.py"],
    ["python", "scripts/check_dashboard_history_feature_ab_preview.py"],
    ["python", "scripts/check_dashboard_history_feature_adapter_preview.py"],
    ["python", "scripts/check_history_feature_prediction_adapter.py"],
    ["python", "scripts/check_history_feature_adapter_preview.py"],
    ["python", "scripts/check_history_feature_shadow_preview.py"],
    ["python", "scripts/check_dashboard_history_feature_shadow_preview.py"],
    ["python", "scripts/check_history_feature_core_shadow_connection_preview.py"],
    ["python", "scripts/check_history_feature_key_normalization_preview.py"],
    ["python", "scripts/check_phase1_mvp_db_schema_preview.py"],
    ["python", "scripts/check_phase1_mvp_db_schema_implementation_plan_preview.py"],
    ["python", "scripts/check_phase1_mvp_db_schema_ddl_preview.py"],
    ["python", "scripts/check_phase1_mvp_db_schema_migration_script_preview.py"],
    ["python", "scripts/check_phase1_mvp_db_schema_migration_draft.py"],
    ["python", "scripts/check_phase1_mvp_db_schema_migration_execution_preview.py"],
    ["python", "scripts/check_phase1_mvp_db_schema_runtime_guard_preview.py"],
    ["python", "scripts/check_phase1_mvp_db_schema_explicit_execution_gate_preview.py"],
]

REQUIRED_FILES = [
    "data/history_sources.json",
    "data/google_sheets_column_mapping.json",
    "data/import/google_sheets/google_sheets_history_profile.json",
    "data/import/history/history_database_summary.json",
    "docs/history_database_summary.json",
    "scripts/build_history_database.py",
    "scripts/export_history_database_summary.py",
    "scripts/build_racer_history_features.py",
    "scripts/check_racer_history_features.py",
    "data/import/history/racer_history_features.csv",
    "scripts/export_racer_history_features_summary.py",
    "scripts/check_racer_history_features_summary.py",
    "docs/racer_history_features_summary.json",
    "docs/index.html",
    "docs/prediction_history_feature_preview.json",
    "docs/history-feature-ab-preview-schema.json",
    "docs/prediction_history_feature_ab_preview.json",
    "data/history_feature_config.json",
    "scripts/check_history_feature_config.py",
    "scripts/history_feature_loader.py",
    "scripts/check_history_feature_loader.py",
    "scripts/check_prediction_history_feature_join.py",
    "scripts/export_prediction_history_feature_preview.py",
    "scripts/check_prediction_history_feature_preview.py",
    "scripts/check_history_feature_ab_preview_schema.py",
    "scripts/export_history_feature_ab_preview.py",
    "scripts/check_history_feature_ab_preview.py",
    "scripts/check_dashboard_history_feature_summary.py",
    "scripts/check_dashboard_history_feature_ab_preview.py",
    "scripts/check_dashboard_history_feature_adapter_preview.py",
    "scripts/history_feature_prediction_adapter.py",
    "scripts/export_history_feature_adapter_preview.py",
    "docs/prediction_history_feature_adapter_preview.json",
    "scripts/check_history_feature_shadow_preview.py",
    "docs/prediction_history_feature_shadow_preview.json",
    "scripts/check_dashboard_history_feature_shadow_preview.py",
    "scripts/check_history_feature_core_shadow_connection_preview.py",
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

REQUIRED_RESULT_CSV_GLOB = "data/import/history/results/results_*.csv"


def main():
    errors = []

    for path in REQUIRED_FILES:
        if not Path(path).exists():
            errors.append(f"missing required file: {path}")

    result_files = sorted(Path("data/import/history/results").glob("results_*.csv"))
    if not result_files:
        errors.append(f"missing result CSV files: {REQUIRED_RESULT_CSV_GLOB}")

    if errors:
        print("History database readiness validation: FAILED")
        for error in errors:
            print("ERROR: " + error)
        raise SystemExit(1)

    for command in CHECKS:
        print("$ " + " ".join(command))
        completed = subprocess.run(command)
        if completed.returncode != 0:
            print("History database readiness validation: FAILED")
            print("ERROR: command failed: " + " ".join(command))
            raise SystemExit(completed.returncode)

    print("=== STEP 158-D protected prediction restore before STEP 158-C ===")
    _step158d_restore_proc = __import__("subprocess").run(
        ["git", "restore", "--source=HEAD", "--worktree", "docs/prediction.json"],
        text=True,
        stdout=__import__("subprocess").PIPE,
        stderr=__import__("subprocess").STDOUT,
    )
    if _step158d_restore_proc.returncode != 0:
        print(_step158d_restore_proc.stdout, end="")
        raise SystemExit("ERROR: failed to restore docs/prediction.json before STEP 158-C readiness")
    _step158d_cached_restore_proc = __import__("subprocess").run(
        ["git", "restore", "--source=HEAD", "--staged", "docs/prediction.json"],
        text=True,
        stdout=__import__("subprocess").PIPE,
        stderr=__import__("subprocess").STDOUT,
    )
    if _step158d_cached_restore_proc.returncode != 0:
        print(_step158d_cached_restore_proc.stdout, end="")
        raise SystemExit("ERROR: failed to unstage docs/prediction.json before STEP 158-C readiness")
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
    print("History database readiness validation: OK")
    print("STEP 112 CHECK: OK")


if __name__ == "__main__":
    main()
