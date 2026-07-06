#!/usr/bin/env python3
"""
STEP155-C: Validate Phase 1 MVP DB schema migration execution preview.

This checker validates:
- docs/phase1_mvp_db_schema_migration_execution_preview.json

It verifies that the execution preview is preview-only and does not execute migration,
does not execute DDL, does not write DB/schema/prediction/config files, and keeps
Phase 1 MVP migration safety policy.

This checker must not modify:
- db/schema.sql
- db/boatrace.sqlite3
- docs/prediction.json
- data/history_feature_config.json
- scripts/migrate_phase1_mvp_db_schema.py
- scripts/check_phase1_mvp_db_schema_migration_draft.py
- scripts/export_phase1_mvp_db_schema_migration_execution_preview.py
- docs/phase1_mvp_db_schema_migration_execution_preview.json
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


PREVIEW_PATH = Path("docs/phase1_mvp_db_schema_migration_execution_preview.json")
EXPORTER_PATH = Path("scripts/export_phase1_mvp_db_schema_migration_execution_preview.py")
DRAFT_SCRIPT_PATH = Path("scripts/migrate_phase1_mvp_db_schema.py")
DRAFT_CHECKER_PATH = Path("scripts/check_phase1_mvp_db_schema_migration_draft.py")

SCHEMA_SQL_PATH = Path("db/schema.sql")
DB_PATH = Path("db/boatrace.sqlite3")
PREDICTION_PATH = Path("docs/prediction.json")
CONFIG_PATH = Path("data/history_feature_config.json")

REQUIRED_MINIMAL_TABLES = [
    "races",
    "entries",
    "feature_sets",
    "prediction_runs",
    "predictions",
    "results",
    "payouts",
    "stage_metrics",
]

REQUIRED_FALSE_FLAGS = [
    "executes_ddl",
    "writes_database",
    "writes_schema_sql",
    "creates_tables",
    "alters_tables",
    "drops_tables",
    "runs_migration",
    "modifies_prediction_json",
    "writes_prediction_json",
    "prediction_core_connected",
    "config_enabled",
    "history_features_enabled",
]

REQUIRED_FUTURE_EXECUTION_TRUE_KEYS = [
    "explicit_execution_flag_required",
    "default_mode_must_remain_dry_run",
    "clean_git_status_required",
    "sqlite_backup_required",
    "protected_file_hash_record_required",
    "readiness_checks_required",
    "create_table_if_not_exists_only",
    "destructive_sql_forbidden",
    "preserve_history_tables",
    "prediction_json_write_forbidden",
    "config_enablement_forbidden",
    "prediction_core_connection_forbidden",
    "automatic_betting_forbidden",
    "execution_must_be_separate_explicit_step",
]

REQUIRED_FORBIDDEN_SQL_PATTERNS = [
    "DROP TABLE",
    "DROP INDEX",
    "ALTER TABLE",
    "INSERT INTO",
    "UPDATE ",
    "DELETE FROM",
    "REPLACE INTO",
    "TRUNCATE",
]

REQUIRED_ROLLBACK_TRUE_KEYS = [
    "sqlite_backup_required",
    "restore_sqlite_backup",
    "git_restore_tracked_files",
    "record_git_status_before_execution",
    "record_commit_hash_before_execution",
    "record_sqlite_table_list_before_execution",
    "record_row_counts_before_execution",
    "do_not_drop_history_races",
    "do_not_drop_history_results",
]

REQUIRED_DEFERRED_FINAL_DESIGN_TABLES = [
    "racer_stats_snapshot",
    "motor_boat_stats_snapshot",
    "venue_bias_daily",
    "weather_water_snapshots",
    "exhibition_snapshots",
    "odds_snapshots",
    "ingestion_runs",
    "prediction_changes",
    "stage_transition_metrics",
    "model_registry",
    "training_runs",
]

REQUIRED_PRE_NIGHT_FORBIDDEN_INFORMATION = [
    "same-day odds",
    "final odds",
    "exhibition data",
    "exhibition_time",
    "same-day weather",
    "same-day water condition",
    "confirmed race outcome",
    "results",
    "payouts",
    "post-race information",
]

PROTECTED_DIFF_PATHS = [
    SCHEMA_SQL_PATH,
    DB_PATH,
    PREDICTION_PATH,
    CONFIG_PATH,
    DRAFT_SCRIPT_PATH,
    DRAFT_CHECKER_PATH,
    EXPORTER_PATH,
    PREVIEW_PATH,
]


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def require_file(path: Path) -> None:
    if not path.exists():
        fail(f"missing required file: {path}")


def load_json(path: Path) -> dict[str, Any]:
    require_file(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path}: {exc}")
    if not isinstance(data, dict):
        fail(f"{path} must contain a JSON object")
    return data


def require_equal(data: dict[str, Any], key: str, expected: Any) -> None:
    actual = data.get(key)
    if actual != expected:
        fail(f"{key} must be {expected!r}, got {actual!r}")


def require_true(data: dict[str, Any], key: str) -> None:
    actual = data.get(key)
    if actual is not True:
        fail(f"{key} must be True, got {actual!r}")


def require_false(data: dict[str, Any], key: str) -> None:
    actual = data.get(key)
    if actual is not False:
        fail(f"{key} must be False, got {actual!r}")


def require_list_equal(data: dict[str, Any], key: str, expected: list[str]) -> None:
    actual = data.get(key)
    if actual != expected:
        fail(f"{key} must be {expected!r}, got {actual!r}")


def require_contains_all(actual: Any, required: list[str], label: str) -> None:
    if not isinstance(actual, list):
        fail(f"{label} must be a list, got {type(actual).__name__}")
    missing = [item for item in required if item not in actual]
    if missing:
        fail(f"{label} missing required values: {missing!r}")


def git_diff_modified(path: Path) -> bool:
    result = subprocess.run(
        ["git", "diff", "--quiet", "--", str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode != 0


def require_not_modified(path: Path, label: str) -> bool:
    require_file(path)
    modified = git_diff_modified(path)
    if modified:
        fail(f"{label} has uncommitted diff: {path}")
    return modified


def validate_config_disabled() -> None:
    config = load_json(CONFIG_PATH)
    if bool(config.get("enabled", False)):
        fail("data/history_feature_config.json enabled must remain false")


def validate_basic_fields(data: dict[str, Any]) -> None:
    require_equal(data, "step", "STEP155-B")
    require_equal(data, "preview_type", "phase1-mvp-db-schema-migration-execution-preview")
    require_equal(data, "connection_mode", "execution-preview-only")
    require_true(data, "safe_mode")
    require_true(data, "execution_preview_only")
    require_equal(data, "migration_execution_mode", "not-executed")
    require_equal(data, "ddl_execution_mode", "not-executed")

    for flag in REQUIRED_FALSE_FLAGS:
        require_false(data, flag)

    require_equal(data, "minimal_table_count", 8)
    require_list_equal(data, "minimal_tables", REQUIRED_MINIMAL_TABLES)
    require_list_equal(data, "implementation_order", REQUIRED_MINIMAL_TABLES)


def validate_draft_alignment(data: dict[str, Any]) -> tuple[int, int]:
    draft = data.get("draft_alignment")
    if not isinstance(draft, dict):
        fail("draft_alignment must be an object")

    if draft.get("draft_script") != str(DRAFT_SCRIPT_PATH):
        fail(f"draft_alignment.draft_script must be {DRAFT_SCRIPT_PATH}")

    if draft.get("draft_mode") != "dry-run":
        fail(f"draft_alignment.draft_mode must be dry-run, got {draft.get('draft_mode')!r}")

    if draft.get("draft_step") != "STEP154-B":
        fail(f"draft_alignment.draft_step must be STEP154-B, got {draft.get('draft_step')!r}")

    if draft.get("draft_checker") != "STEP154-C":
        fail(f"draft_alignment.draft_checker must be STEP154-C, got {draft.get('draft_checker')!r}")

    ddl_audit = draft.get("ddl_candidates_audit")
    if not isinstance(ddl_audit, dict):
        fail("draft_alignment.ddl_candidates_audit must be an object")

    table_count = ddl_audit.get("table_count")
    danger_pattern_count = ddl_audit.get("danger_pattern_count")

    if table_count != 8:
        fail(f"ddl_candidates_audit.table_count must be 8, got {table_count!r}")

    if danger_pattern_count != 0:
        fail(f"ddl_candidates_audit.danger_pattern_count must be 0, got {danger_pattern_count!r}")

    if ddl_audit.get("ddl_candidates_audit_ok") is not True:
        fail("ddl_candidates_audit.ddl_candidates_audit_ok must be True")

    if ddl_audit.get("danger_patterns") != "NONE":
        fail(f"ddl_candidates_audit.danger_patterns must be NONE, got {ddl_audit.get('danger_patterns')!r}")

    tables = ddl_audit.get("tables")
    if tables != REQUIRED_MINIMAL_TABLES:
        fail(f"ddl_candidates_audit.tables must be {REQUIRED_MINIMAL_TABLES!r}, got {tables!r}")

    table_audits = ddl_audit.get("table_audits")
    if not isinstance(table_audits, list):
        fail("ddl_candidates_audit.table_audits must be a list")

    if len(table_audits) != 8:
        fail(f"ddl_candidates_audit.table_audits length must be 8, got {len(table_audits)}")

    for item in table_audits:
        if not isinstance(item, dict):
            fail("each table_audits item must be an object")
        table = item.get("table")
        if table not in REQUIRED_MINIMAL_TABLES:
            fail(f"unexpected DDL audit table: {table!r}")
        if item.get("has_create_table_if_not_exists") is not True:
            fail(f"{table} must have has_create_table_if_not_exists=True")
        if item.get("danger_hits") != []:
            fail(f"{table} danger_hits must be empty list, got {item.get('danger_hits')!r}")
        if item.get("candidate_statement_type") != "CREATE TABLE IF NOT EXISTS":
            fail(f"{table} candidate_statement_type must be CREATE TABLE IF NOT EXISTS")

    runtime = draft.get("draft_runtime_validation")
    if not isinstance(runtime, dict) or runtime.get("draft_runtime_ok") is not True:
        fail("draft_runtime_validation.draft_runtime_ok must be True")

    checker = draft.get("draft_checker_validation")
    if not isinstance(checker, dict) or checker.get("draft_checker_ok") is not True:
        fail("draft_checker_validation.draft_checker_ok must be True")

    return int(table_count), int(danger_pattern_count)


def validate_future_execution_requirements(data: dict[str, Any]) -> None:
    req = data.get("future_execution_mode_requirements")
    if not isinstance(req, dict):
        fail("future_execution_mode_requirements must be an object")

    for key in REQUIRED_FUTURE_EXECUTION_TRUE_KEYS:
        if req.get(key) is not True:
            fail(f"future_execution_mode_requirements.{key} must be True, got {req.get(key)!r}")

    if req.get("future_candidate_statement") != "CREATE TABLE IF NOT EXISTS":
        fail(
            "future_execution_mode_requirements.future_candidate_statement "
            "must be CREATE TABLE IF NOT EXISTS"
        )

    history_tables = req.get("history_tables_to_preserve")
    require_contains_all(history_tables, ["history_races", "history_results"], "history_tables_to_preserve")


def validate_forbidden_sql_patterns(data: dict[str, Any]) -> None:
    patterns = data.get("forbidden_sql_patterns")
    require_contains_all(patterns, REQUIRED_FORBIDDEN_SQL_PATTERNS, "forbidden_sql_patterns")

    if "UPDATE" in patterns and "UPDATE " not in patterns:
        fail("forbidden_sql_patterns must use 'UPDATE ' with trailing space to avoid updated_at false positive")

    if "UPDATE " not in patterns:
        fail("forbidden_sql_patterns must contain 'UPDATE ' with trailing space")


def validate_rollback_requirements(data: dict[str, Any]) -> None:
    rollback = data.get("rollback_requirements")
    if not isinstance(rollback, dict):
        fail("rollback_requirements must be an object")

    for key in REQUIRED_ROLLBACK_TRUE_KEYS:
        if rollback.get(key) is not True:
            fail(f"rollback_requirements.{key} must be True, got {rollback.get(key)!r}")

    record_files = rollback.get("record_sha256_files")
    require_contains_all(
        record_files,
        [
            str(SCHEMA_SQL_PATH),
            str(DB_PATH),
            str(PREDICTION_PATH),
            str(CONFIG_PATH),
        ],
        "rollback_requirements.record_sha256_files",
    )


def validate_key_policy(data: dict[str, Any]) -> tuple[str, str]:
    key_policy = data.get("key_policy")
    if not isinstance(key_policy, dict):
        fail("key_policy must be an object")

    race_id_policy = key_policy.get("race_id_policy")
    canonical_candidate_key_policy = key_policy.get("canonical_candidate_key_policy")

    if race_id_policy != "race_id = canonical_race_key":
        fail(f"race_id_policy must be 'race_id = canonical_race_key', got {race_id_policy!r}")

    if canonical_candidate_key_policy != 'canonical_candidate_key = race_id + "_" + lane':
        fail(
            "canonical_candidate_key_policy must be "
            "'canonical_candidate_key = race_id + \"_\" + lane', "
            f"got {canonical_candidate_key_policy!r}"
        )

    if key_policy.get("canonical_race_key") != 'race_date + "_" + venue_id + "_" + race_no':
        fail("canonical_race_key policy mismatch")

    if key_policy.get("canonical_candidate_key") != 'race_id + "_" + lane':
        fail("canonical_candidate_key policy mismatch")

    return str(race_id_policy), str(canonical_candidate_key_policy)


def validate_pdf_constraints(data: dict[str, Any]) -> None:
    pdf = data.get("pdf_operation_constraints")
    if not isinstance(pdf, dict):
        fail("pdf_operation_constraints must be an object")

    if pdf.get("no_automatic_betting") is not True:
        fail("pdf_operation_constraints.no_automatic_betting must be True")

    if pdf.get("collection_interval_policy") != "5 to 15 minutes":
        fail("collection_interval_policy must be 5 to 15 minutes")

    if pdf.get("sqlite_commit_policy") != "nightly SQLite merge":
        fail("sqlite_commit_policy must be nightly SQLite merge")

    if pdf.get("llm_usage_policy") != "LLM not used for normal prediction":
        fail("llm_usage_policy must be LLM not used for normal prediction")

    if pdf.get("smartphone_centric_operation") is not True:
        fail("smartphone_centric_operation must be True")


def validate_final_design_compatibility(data: dict[str, Any]) -> None:
    compat = data.get("final_design_pdf_compatibility")
    if not isinstance(compat, dict):
        fail("final_design_pdf_compatibility must be an object")

    if compat.get("phase1_is_safe_subset_of_final_design") is not True:
        fail("phase1_is_safe_subset_of_final_design must be True")

    if compat.get("deferred_tables_not_created_in_step155_b") is not True:
        fail("deferred_tables_not_created_in_step155_b must be True")

    require_contains_all(
        compat.get("deferred_final_design_tables"),
        REQUIRED_DEFERRED_FINAL_DESIGN_TABLES,
        "deferred_final_design_tables",
    )


def validate_pre_night_constraints(data: dict[str, Any]) -> None:
    pre = data.get("pre_night_safety_constraints")
    if not isinstance(pre, dict):
        fail("pre_night_safety_constraints must be an object")

    if pre.get("pre_night_only") is not True:
        fail("pre_night_only must be True")

    if pre.get("results_and_payouts_allowed_as_pre_night_inputs") is not False:
        fail("results_and_payouts_allowed_as_pre_night_inputs must be False")

    require_contains_all(
        pre.get("forbidden_information"),
        REQUIRED_PRE_NIGHT_FORBIDDEN_INFORMATION,
        "pre_night_safety_constraints.forbidden_information",
    )


def validate_previous_preview_validation(data: dict[str, Any]) -> None:
    prev = data.get("previous_preview_validation")
    if not isinstance(prev, dict):
        fail("previous_preview_validation must be an object")

    migration = prev.get("migration_script_preview")
    if not isinstance(migration, dict):
        fail("previous_preview_validation.migration_script_preview must be an object")

    if migration.get("step") != "STEP153-B":
        fail("previous migration script preview step must be STEP153-B")

    if migration.get("preview_type") != "phase1-mvp-db-schema-migration-script-preview":
        fail("previous migration script preview_type mismatch")

    if migration.get("connection_mode") != "migration-preview-only":
        fail("previous migration script connection_mode mismatch")

    if migration.get("minimal_table_count") != 8:
        fail("previous migration script minimal_table_count must be 8")

    ddl = prev.get("ddl_preview")
    if not isinstance(ddl, dict):
        fail("previous_preview_validation.ddl_preview must be an object")

    if ddl.get("step") != "STEP152-B":
        fail("previous DDL preview step must be STEP152-B")

    if ddl.get("preview_type") != "phase1-mvp-db-schema-ddl-preview":
        fail("previous DDL preview_type mismatch")

    if ddl.get("connection_mode") != "ddl-preview-only":
        fail("previous DDL preview connection_mode mismatch")

    if ddl.get("minimal_table_count") != 8:
        fail("previous DDL preview minimal_table_count must be 8")


def validate_step155a_reference(data: dict[str, Any]) -> None:
    ref = data.get("step155a_audit_reference")
    if not isinstance(ref, dict):
        fail("step155a_audit_reference must be an object")

    if ref.get("expected_files_present") is not True:
        fail("step155a_audit_reference.expected_files_present must be True")

    if ref.get("required_markers_present") is not True:
        fail("step155a_audit_reference.required_markers_present must be True")

    if ref.get("missing_files") not in ([], None):
        fail(f"step155a_audit_reference.missing_files must be empty, got {ref.get('missing_files')!r}")

    if ref.get("missing_markers") not in ([], None):
        fail(f"step155a_audit_reference.missing_markers must be empty, got {ref.get('missing_markers')!r}")


def validate_safety_decisions(data: dict[str, Any]) -> None:
    decisions = data.get("safety_decisions")
    if not isinstance(decisions, dict):
        fail("safety_decisions must be an object")

    required_true = [
        "do_not_modify_draft_script_in_step155_b",
        "do_not_modify_checker_in_step155_b",
        "do_not_modify_readiness_scripts_in_step155_b",
        "do_not_modify_schema_sql_in_step155_b",
        "do_not_modify_sqlite_db_in_step155_b",
        "do_not_modify_prediction_json_in_step155_b",
        "do_not_enable_history_features_in_step155_b",
        "do_not_connect_prediction_core_in_step155_b",
        "do_not_execute_migration_in_step155_b",
        "do_not_execute_ddl_in_step155_b",
    ]

    for key in required_true:
        if decisions.get(key) is not True:
            fail(f"safety_decisions.{key} must be True, got {decisions.get(key)!r}")


def validate_protected_file_diffs() -> dict[str, bool]:
    states: dict[str, bool] = {}

    for path in PROTECTED_DIFF_PATHS:
        label = str(path)
        modified = require_not_modified(path, label)
        states[label] = modified

    return states


def main() -> None:
    for path in [
        PREVIEW_PATH,
        EXPORTER_PATH,
        DRAFT_SCRIPT_PATH,
        DRAFT_CHECKER_PATH,
        SCHEMA_SQL_PATH,
        DB_PATH,
        PREDICTION_PATH,
        CONFIG_PATH,
    ]:
        require_file(path)

    validate_config_disabled()

    data = load_json(PREVIEW_PATH)

    validate_basic_fields(data)
    table_count, danger_pattern_count = validate_draft_alignment(data)
    validate_future_execution_requirements(data)
    validate_forbidden_sql_patterns(data)
    validate_rollback_requirements(data)
    race_id_policy, canonical_candidate_key_policy = validate_key_policy(data)
    validate_pdf_constraints(data)
    validate_final_design_compatibility(data)
    validate_pre_night_constraints(data)
    validate_previous_preview_validation(data)
    validate_step155a_reference(data)
    validate_safety_decisions(data)

    clean_states = validate_protected_file_diffs()

    schema_sql_modified = clean_states[str(SCHEMA_SQL_PATH)]
    database_modified = clean_states[str(DB_PATH)]
    prediction_json_modified = clean_states[str(PREDICTION_PATH)]
    config_modified = clean_states[str(CONFIG_PATH)]
    execution_preview_modified = clean_states[str(PREVIEW_PATH)]

    print("Phase 1 MVP DB schema migration execution preview validation: OK")
    print("STEP 155-C CHECK: OK")
    print(f"preview_type={data['preview_type']}")
    print(f"connection_mode={data['connection_mode']}")
    print(f"execution_preview_only={data['execution_preview_only']}")
    print(f"migration_execution_mode={data['migration_execution_mode']}")
    print(f"ddl_execution_mode={data['ddl_execution_mode']}")
    print(f"executes_ddl={data['executes_ddl']}")
    print(f"writes_database={data['writes_database']}")
    print(f"writes_schema_sql={data['writes_schema_sql']}")
    print(f"creates_tables={data['creates_tables']}")
    print(f"alters_tables={data['alters_tables']}")
    print(f"drops_tables={data['drops_tables']}")
    print(f"runs_migration={data['runs_migration']}")
    print(f"modifies_prediction_json={data['modifies_prediction_json']}")
    print(f"writes_prediction_json={data['writes_prediction_json']}")
    print(f"prediction_core_connected={data['prediction_core_connected']}")
    print(f"config_enabled={data['config_enabled']}")
    print(f"history_features_enabled={data['history_features_enabled']}")
    print(f"minimal_table_count={data['minimal_table_count']}")
    print("draft_mode=dry-run")
    print(f"ddl_candidates_table_count={table_count}")
    print(f"ddl_candidates_danger_pattern_count={danger_pattern_count}")
    print(f"race_id_policy={race_id_policy}")
    print(f"canonical_candidate_key_policy={canonical_candidate_key_policy}")
    print("no_automatic_betting=True")
    print("collection_interval_policy=5 to 15 minutes")
    print("sqlite_commit_policy=nightly SQLite merge")
    print("llm_usage_policy=LLM not used for normal prediction")
    print(f"schema_sql_currently_modified={schema_sql_modified}")
    print(f"database_currently_modified={database_modified}")
    print(f"prediction_json_currently_modified={prediction_json_modified}")
    print(f"config_currently_modified={config_modified}")
    print(f"execution_preview_currently_modified={execution_preview_modified}")


if __name__ == "__main__":
    main()
