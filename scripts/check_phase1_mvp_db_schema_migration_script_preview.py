#!/usr/bin/env python3
"""
STEP153-C: Validate Phase 1 MVP DB schema migration script preview.

This checker validates:
- docs/phase1_mvp_db_schema_migration_script_preview.json

It must not modify:
- db/schema.sql
- db/boatrace.sqlite3
- docs/prediction.json
- data/history_feature_config.json
- docs/phase1_mvp_db_schema_migration_script_preview.json
- docs/phase1_mvp_db_schema_ddl_preview.json

It must not create or execute migration scripts.
It must not execute DDL.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


CONFIG_PATH = Path("data/history_feature_config.json")
PREDICTION_PATH = Path("docs/prediction.json")
SCHEMA_SQL_PATH = Path("db/schema.sql")
DB_PATH = Path("db/boatrace.sqlite3")
DDL_PREVIEW_PATH = Path("docs/phase1_mvp_db_schema_ddl_preview.json")
EXPORTER_PATH = Path("scripts/export_phase1_mvp_db_schema_migration_script_preview.py")
PREVIEW_PATH = Path("docs/phase1_mvp_db_schema_migration_script_preview.json")

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

REQUIRED_DEFERRED_TABLES = [
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

REQUIRED_HISTORY_TABLES = [
    "history_races",
    "history_results",
]

REQUIRED_FALSE_FLAGS = [
    "config_enabled",
    "history_features_enabled",
    "prediction_core_connected",
    "modifies_prediction_json",
    "writes_prediction_json",
    "writes_schema_sql",
    "writes_database",
    "creates_tables",
    "alters_tables",
    "drops_tables",
    "runs_migration",
    "executes_ddl",
    "creates_migration_script",
]

REQUIRED_FORBIDDEN_INFORMATION = [
    "same-day odds",
    "final odds",
    "exhibition data",
    "same-day weather",
    "same-day water condition",
    "results",
    "payouts",
    "post-race information",
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


def git_diff_modified(path: Path) -> bool:
    result = subprocess.run(
        ["git", "diff", "--quiet", "--", str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode != 0


def require_not_modified(path: Path, label: str) -> None:
    if git_diff_modified(path):
        fail(f"{label} has uncommitted diff: {path}")


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


def require_contains_all(values: Any, required: list[str], label: str) -> None:
    if not isinstance(values, list):
        fail(f"{label} must be list, got {type(values).__name__}")
    missing = [item for item in required if item not in values]
    if missing:
        fail(f"{label} missing required values: {missing!r}")


def validate_source_files(data: dict[str, Any]) -> None:
    source_files = data.get("source_files")
    if not isinstance(source_files, dict):
        fail("source_files must be object")

    expected = {
        "config": str(CONFIG_PATH),
        "prediction_json": str(PREDICTION_PATH),
        "schema_sql": str(SCHEMA_SQL_PATH),
        "sqlite_database": str(DB_PATH),
        "ddl_preview": str(DDL_PREVIEW_PATH),
    }

    for key, expected_value in expected.items():
        actual = source_files.get(key)
        if actual != expected_value:
            fail(f"source_files.{key} must be {expected_value!r}, got {actual!r}")


def validate_migration_script_design_direction(data: dict[str, Any]) -> None:
    direction = data.get("migration_script_design_direction")
    if not isinstance(direction, dict):
        fail("migration_script_design_direction must be object")

    required_true = [
        "add_only",
        "idempotent",
        "guarded_by_safety_checks",
        "requires_pre_migration_hash_record",
        "requires_sqlite_backup_before_execution",
    ]

    required_false = [
        "drop_table_allowed",
        "drop_index_allowed",
        "destructive_alter_allowed",
        "delete_from_history_tables_allowed",
        "update_history_tables_allowed",
        "replace_into_history_tables_allowed",
        "migration_execution_allowed_in_this_step",
        "schema_sql_write_allowed_in_this_step",
        "sqlite_write_allowed_in_this_step",
        "migration_script_file_created_in_this_step",
    ]

    for key in required_true:
        if direction.get(key) is not True:
            fail(f"migration_script_design_direction.{key} must be True")

    for key in required_false:
        if direction.get(key) is not False:
            fail(f"migration_script_design_direction.{key} must be False")

    if direction.get("future_candidate_statement") != "CREATE TABLE IF NOT EXISTS":
        fail(
            "migration_script_design_direction.future_candidate_statement must be "
            "'CREATE TABLE IF NOT EXISTS'"
        )


def validate_ddl_candidate_audit(data: dict[str, Any]) -> None:
    audit = data.get("ddl_candidate_audit")
    if not isinstance(audit, list):
        fail("ddl_candidate_audit must be list")
    if len(audit) != 8:
        fail(f"ddl_candidate_audit must contain 8 items, got {len(audit)}")

    names = []
    for i, item in enumerate(audit):
        if not isinstance(item, dict):
            fail(f"ddl_candidate_audit[{i}] must be object")

        name = item.get("table_name")
        names.append(name)

        if name not in REQUIRED_MINIMAL_TABLES:
            fail(f"ddl_candidate_audit[{i}].table_name unexpected: {name!r}")

        if item.get("has_create_table_if_not_exists") is not True:
            fail(f"ddl_candidate_audit[{i}].has_create_table_if_not_exists must be True")

        if item.get("danger_pattern_count") != 0:
            fail(f"ddl_candidate_audit[{i}].danger_pattern_count must be 0")

        danger_patterns = item.get("danger_patterns")
        if danger_patterns != []:
            fail(f"ddl_candidate_audit[{i}].danger_patterns must be []")

        if item.get("candidate_ddl_not_executed") is not True:
            fail(f"ddl_candidate_audit[{i}].candidate_ddl_not_executed must be True")

    if names != REQUIRED_MINIMAL_TABLES:
        fail(f"ddl_candidate_audit order mismatch: {names!r}")


def validate_key_policy(data: dict[str, Any]) -> None:
    policy = data.get("key_policy")
    if not isinstance(policy, dict):
        fail("key_policy must be object")

    if policy.get("race_id_policy") != "race_id = canonical_race_key":
        fail("key_policy.race_id_policy must be 'race_id = canonical_race_key'")

    if policy.get("canonical_candidate_key_policy") != "canonical_candidate_key = race_id + '_' + lane":
        fail(
            "key_policy.canonical_candidate_key_policy must be "
            "\"canonical_candidate_key = race_id + '_' + lane\""
        )

    race_key = policy.get("canonical_race_key")
    candidate_key = policy.get("canonical_candidate_key")

    if not isinstance(race_key, dict):
        fail("key_policy.canonical_race_key must be object")
    if not isinstance(candidate_key, dict):
        fail("key_policy.canonical_candidate_key must be object")

    if race_key.get("components") != ["race_date", "venue_id", "race_no"]:
        fail("canonical_race_key components mismatch")

    if candidate_key.get("components") != ["race_date", "venue_id", "race_no", "lane"]:
        fail("canonical_candidate_key components mismatch")

    mapping = policy.get("pdf_entries_primary_key_mapping")
    if not isinstance(mapping, dict):
        fail("key_policy.pdf_entries_primary_key_mapping must be object")

    if mapping.get("pdf_primary_key") != ["race_id", "lane"]:
        fail("pdf_entries_primary_key_mapping.pdf_primary_key mismatch")

    if mapping.get("phase1_equivalent") != "canonical_candidate_key":
        fail("pdf_entries_primary_key_mapping.phase1_equivalent mismatch")

    require_contains_all(
        policy.get("not_primary_key_components"),
        [
            "racer_name",
            "motor_no",
            "boat_no",
            "odds",
            "exhibition_time",
            "weather",
            "result",
            "payout",
        ],
        "key_policy.not_primary_key_components",
    )


def validate_existing_history_tables_policy(data: dict[str, Any]) -> None:
    policy = data.get("existing_history_tables_policy")
    if not isinstance(policy, dict):
        fail("existing_history_tables_policy must be object")

    if policy.get("policy") != "preserve":
        fail("existing_history_tables_policy.policy must be preserve")

    if policy.get("existing_history_tables_preserved") is not True:
        fail("existing_history_tables_policy.existing_history_tables_preserved must be True")

    require_contains_all(policy.get("tables"), REQUIRED_HISTORY_TABLES, "existing_history_tables_policy.tables")

    for key in [
        "drop_allowed",
        "recreate_allowed",
        "destructive_alter_allowed",
        "delete_allowed",
        "update_allowed",
    ]:
        if policy.get(key) is not False:
            fail(f"existing_history_tables_policy.{key} must be False")


def validate_final_design_pdf_compatibility(data: dict[str, Any]) -> None:
    pdf = data.get("final_design_pdf_compatibility")
    if not isinstance(pdf, dict):
        fail("final_design_pdf_compatibility must be object")

    if pdf.get("phase1_is_safe_subset_of_final_design") is not True:
        fail("phase1_is_safe_subset_of_final_design must be True")

    require_contains_all(
        pdf.get("covered_phase1_tables"),
        REQUIRED_MINIMAL_TABLES,
        "final_design_pdf_compatibility.covered_phase1_tables",
    )

    require_contains_all(
        pdf.get("deferred_final_design_tables"),
        REQUIRED_DEFERRED_TABLES,
        "final_design_pdf_compatibility.deferred_final_design_tables",
    )

    if pdf.get("deferred_tables_not_forgotten") is not True:
        fail("deferred_tables_not_forgotten must be True")

    phase_mapping = pdf.get("phase_mapping")
    if not isinstance(phase_mapping, dict):
        fail("final_design_pdf_compatibility.phase_mapping must be object")

    for phase in ["Phase 1", "Phase 2", "Phase 3", "Phase 4", "Phase 5"]:
        if phase not in phase_mapping:
            fail(f"final_design_pdf_compatibility.phase_mapping missing {phase}")


def validate_pdf_operation_constraints(data: dict[str, Any]) -> None:
    constraints = data.get("pdf_operation_constraints")
    if not isinstance(constraints, dict):
        fail("pdf_operation_constraints must be object")

    expected = {
        "no_automatic_betting": True,
        "avoid_high_frequency_fetching": True,
        "cache_fetched_data": True,
        "fallback_on_failure": True,
        "smartphone_operation_supported": True,
    }

    for key, expected_value in expected.items():
        if constraints.get(key) is not expected_value:
            fail(f"pdf_operation_constraints.{key} must be {expected_value!r}")

    if constraints.get("collection_interval_policy") != "5 to 15 minutes":
        fail("collection_interval_policy must be '5 to 15 minutes'")

    if constraints.get("intraday_updates") != "JSON-centered updates":
        fail("intraday_updates must be 'JSON-centered updates'")

    if constraints.get("sqlite_commit_policy") != "nightly SQLite merge":
        fail("sqlite_commit_policy must be 'nightly SQLite merge'")

    if constraints.get("llm_usage_policy") != "LLM not used for normal prediction":
        fail("llm_usage_policy must be 'LLM not used for normal prediction'")

    if constraints.get("llm_allowed_scope") != "weekly evaluation analysis only":
        fail("llm_allowed_scope must be 'weekly evaluation analysis only'")


def validate_pre_night_safety_constraints(data: dict[str, Any]) -> None:
    constraints = data.get("pre_night_safety_constraints")
    if not isinstance(constraints, dict):
        fail("pre_night_safety_constraints must be object")

    if constraints.get("pre_night_only") is not True:
        fail("pre_night_safety_constraints.pre_night_only must be True")

    if constraints.get("results_and_payouts_allowed_as_pre_night_inputs") is not False:
        fail("results_and_payouts_allowed_as_pre_night_inputs must be False")

    if constraints.get("results_and_payouts_allowed_as_training_labels_after_race") is not True:
        fail("results_and_payouts_allowed_as_training_labels_after_race must be True")

    require_contains_all(
        constraints.get("forbidden_information"),
        REQUIRED_FORBIDDEN_INFORMATION,
        "pre_night_safety_constraints.forbidden_information",
    )


def validate_rollback_requirements(data: dict[str, Any]) -> None:
    rollback = data.get("rollback_requirements_for_future_migration")
    if not isinstance(rollback, dict):
        fail("rollback_requirements_for_future_migration must be object")

    required_true = [
        "record_git_status",
        "record_git_hash",
        "record_schema_sql_sha256",
        "record_sqlite_db_sha256",
        "record_prediction_json_sha256",
        "record_config_sha256",
        "record_existing_sqlite_table_list",
        "record_history_races_row_count",
        "record_history_results_row_count",
        "create_sqlite_backup_before_execution",
        "restore_path_required",
    ]

    for key in required_true:
        if rollback.get(key) is not True:
            fail(f"rollback_requirements_for_future_migration.{key} must be True")


def validate_current_repository_state(data: dict[str, Any]) -> None:
    state = data.get("current_repository_state")
    if not isinstance(state, dict):
        fail("current_repository_state must be object")

    schema_sql = state.get("schema_sql")
    sqlite_database = state.get("sqlite_database")

    if not isinstance(schema_sql, dict):
        fail("current_repository_state.schema_sql must be object")
    if not isinstance(sqlite_database, dict):
        fail("current_repository_state.sqlite_database must be object")

    if schema_sql.get("exists") is not True:
        fail("current_repository_state.schema_sql.exists must be True")
    if sqlite_database.get("exists") is not True:
        fail("current_repository_state.sqlite_database.exists must be True")

    history_presence = sqlite_database.get("history_table_presence")
    if not isinstance(history_presence, dict):
        fail("current_repository_state.sqlite_database.history_table_presence must be object")

    for table in REQUIRED_HISTORY_TABLES:
        if history_presence.get(table) is not True:
            fail(f"history table must exist in sqlite inspection: {table}")

    for key in [
        "prediction_json_currently_modified",
        "config_currently_modified",
        "ddl_preview_currently_modified",
    ]:
        if state.get(key) is not False:
            fail(f"current_repository_state.{key} must be False")


def validate_previous_preview_validation(data: dict[str, Any]) -> None:
    previous = data.get("previous_preview_validation")
    if not isinstance(previous, dict):
        fail("previous_preview_validation must be object")

    ddl = previous.get("ddl_preview")
    if not isinstance(ddl, dict):
        fail("previous_preview_validation.ddl_preview must be object")

    if ddl.get("step") != "STEP152-B":
        fail("previous_preview_validation.ddl_preview.step must be STEP152-B")
    if ddl.get("preview_type") != "phase1-mvp-db-schema-ddl-preview":
        fail("previous_preview_validation.ddl_preview.preview_type mismatch")
    if ddl.get("connection_mode") != "ddl-preview-only":
        fail("previous_preview_validation.ddl_preview.connection_mode mismatch")
    if ddl.get("ddl_execution_mode") != "not-executed":
        fail("previous_preview_validation.ddl_preview.ddl_execution_mode mismatch")
    if ddl.get("ddl_preview_only") is not True:
        fail("previous_preview_validation.ddl_preview.ddl_preview_only must be True")
    if ddl.get("minimal_table_count") != 8:
        fail("previous_preview_validation.ddl_preview.minimal_table_count must be 8")


def validate_safety_decisions(data: dict[str, Any]) -> None:
    safety = data.get("safety_decisions")
    if not isinstance(safety, dict):
        fail("safety_decisions must be object")

    required_true = [
        "do_not_create_migration_script_in_step153_b",
        "do_not_execute_migration_in_step153_b",
        "do_not_execute_ddl_in_step153_b",
        "do_not_modify_schema_sql_in_step153_b",
        "do_not_modify_sqlite_db_in_step153_b",
        "do_not_modify_prediction_json",
        "do_not_modify_ddl_preview_json",
        "do_not_enable_history_features",
        "do_not_connect_prediction_core",
        "do_not_change_prediction_scores_or_ranks",
        "do_not_add_dashboard_ui",
    ]

    for key in required_true:
        if safety.get(key) is not True:
            fail(f"safety_decisions.{key} must be True")


def main() -> None:
    for path in [
        CONFIG_PATH,
        PREDICTION_PATH,
        SCHEMA_SQL_PATH,
        DB_PATH,
        DDL_PREVIEW_PATH,
        EXPORTER_PATH,
        PREVIEW_PATH,
    ]:
        require_file(path)

    config = load_json(CONFIG_PATH)
    if bool(config.get("enabled", False)):
        fail("data/history_feature_config.json enabled must remain false")

    data = load_json(PREVIEW_PATH)

    require_equal(data, "step", "STEP153-B")
    require_equal(data, "preview_type", "phase1-mvp-db-schema-migration-script-preview")
    require_equal(data, "connection_mode", "migration-preview-only")
    require_true(data, "safe_mode")
    require_true(data, "migration_script_preview_only")
    require_equal(data, "migration_script_execution_mode", "not-created-not-executed")
    require_equal(data, "ddl_execution_mode", "not-executed")

    for key in REQUIRED_FALSE_FLAGS:
        require_false(data, key)

    require_equal(data, "minimal_table_count", 8)
    require_list_equal(data, "minimal_tables", REQUIRED_MINIMAL_TABLES)
    require_list_equal(data, "implementation_order", REQUIRED_MINIMAL_TABLES)

    output = data.get("output")
    if output != str(PREVIEW_PATH):
        fail(f"output must be {str(PREVIEW_PATH)!r}, got {output!r}")

    validate_source_files(data)
    validate_migration_script_design_direction(data)
    validate_ddl_candidate_audit(data)
    validate_key_policy(data)
    validate_existing_history_tables_policy(data)
    validate_final_design_pdf_compatibility(data)
    validate_pdf_operation_constraints(data)
    validate_pre_night_safety_constraints(data)
    validate_rollback_requirements(data)
    validate_current_repository_state(data)
    validate_previous_preview_validation(data)
    validate_safety_decisions(data)

    require_not_modified(SCHEMA_SQL_PATH, "db/schema.sql")
    require_not_modified(DB_PATH, "db/boatrace.sqlite3")
    require_not_modified(PREDICTION_PATH, "docs/prediction.json")
    require_not_modified(CONFIG_PATH, "data/history_feature_config.json")
    require_not_modified(DDL_PREVIEW_PATH, "docs/phase1_mvp_db_schema_ddl_preview.json")

    schema_sql_currently_modified = git_diff_modified(SCHEMA_SQL_PATH)
    database_currently_modified = git_diff_modified(DB_PATH)
    prediction_json_currently_modified = git_diff_modified(PREDICTION_PATH)
    config_currently_modified = git_diff_modified(CONFIG_PATH)
    ddl_preview_currently_modified = git_diff_modified(DDL_PREVIEW_PATH)

    key_policy = data["key_policy"]
    pdf_constraints = data["pdf_operation_constraints"]

    print("Phase 1 MVP DB schema migration script preview validation: OK")
    print("STEP 153-C CHECK: OK")
    print(f"preview_type={data['preview_type']}")
    print(f"connection_mode={data['connection_mode']}")
    print(f"config_enabled={data['config_enabled']}")
    print(f"history_features_enabled={data['history_features_enabled']}")
    print(f"prediction_core_connected={data['prediction_core_connected']}")
    print(f"modifies_prediction_json={data['modifies_prediction_json']}")
    print(f"writes_prediction_json={data['writes_prediction_json']}")
    print(f"writes_schema_sql={data['writes_schema_sql']}")
    print(f"writes_database={data['writes_database']}")
    print(f"creates_tables={data['creates_tables']}")
    print(f"alters_tables={data['alters_tables']}")
    print(f"drops_tables={data['drops_tables']}")
    print(f"runs_migration={data['runs_migration']}")
    print(f"executes_ddl={data['executes_ddl']}")
    print(f"creates_migration_script={data['creates_migration_script']}")
    print(f"minimal_table_count={data['minimal_table_count']}")
    print(f"migration_script_preview_only={data['migration_script_preview_only']}")
    print(f"migration_script_execution_mode={data['migration_script_execution_mode']}")
    print(f"ddl_execution_mode={data['ddl_execution_mode']}")
    print(f"race_id_policy={key_policy['race_id_policy']}")
    print(f"collection_interval_policy={pdf_constraints['collection_interval_policy']}")
    print(f"sqlite_commit_policy={pdf_constraints['sqlite_commit_policy']}")
    print(f"llm_usage_policy={pdf_constraints['llm_usage_policy']}")
    print(f"schema_sql_currently_modified={schema_sql_currently_modified}")
    print(f"database_currently_modified={database_currently_modified}")
    print(f"prediction_json_currently_modified={prediction_json_currently_modified}")
    print(f"config_currently_modified={config_currently_modified}")
    print(f"ddl_preview_currently_modified={ddl_preview_currently_modified}")


if __name__ == "__main__":
    main()
