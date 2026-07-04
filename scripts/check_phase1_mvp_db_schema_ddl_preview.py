#!/usr/bin/env python3
"""
STEP152-C: Validate Phase 1 MVP DB schema DDL preview.

This checker validates:
- docs/phase1_mvp_db_schema_ddl_preview.json

It must not modify:
- db/schema.sql
- db/boatrace.sqlite3
- docs/prediction.json
- data/history_feature_config.json
- docs/phase1_mvp_db_schema_ddl_preview.json

It must not execute DDL:
- no CREATE TABLE execution
- no ALTER TABLE execution
- no DROP TABLE execution
- no migration execution
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
EXPORTER_PATH = Path("scripts/export_phase1_mvp_db_schema_ddl_preview.py")
PREVIEW_PATH = Path("docs/phase1_mvp_db_schema_ddl_preview.json")

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

REQUIRED_IMPLEMENTATION_ORDER = [
    "races",
    "entries",
    "feature_sets",
    "prediction_runs",
    "predictions",
    "results",
    "payouts",
    "stage_metrics",
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


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        fail(f"missing required file: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path}: {exc}")
    if not isinstance(data, dict):
        fail(f"{path} must contain a JSON object")
    return data


def require_file(path: Path) -> None:
    if not path.exists():
        fail(f"missing required file: {path}")


def require_equal(data: dict[str, Any], key: str, expected: Any) -> None:
    actual = data.get(key)
    if actual != expected:
        fail(f"{key} must be {expected!r}, got {actual!r}")


def require_false(data: dict[str, Any], key: str) -> None:
    if data.get(key) is not False:
        fail(f"{key} must be False, got {data.get(key)!r}")


def require_true(data: dict[str, Any], key: str) -> None:
    if data.get(key) is not True:
        fail(f"{key} must be True, got {data.get(key)!r}")


def require_list_equal(data: dict[str, Any], key: str, expected: list[str]) -> None:
    actual = data.get(key)
    if actual != expected:
        fail(f"{key} must be {expected!r}, got {actual!r}")


def require_contains_all(values: Any, required: list[str], label: str) -> None:
    if not isinstance(values, list):
        fail(f"{label} must be a list, got {type(values).__name__}")
    missing = [item for item in required if item not in values]
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


def require_not_modified(path: Path, label: str) -> None:
    if git_diff_modified(path):
        fail(f"{label} has uncommitted diff: {path}")


def validate_source_files(data: dict[str, Any]) -> None:
    source_files = data.get("source_files")
    if not isinstance(source_files, dict):
        fail("source_files must be object")

    expected = {
        "config": str(CONFIG_PATH),
        "prediction_json": str(PREDICTION_PATH),
        "schema_sql": str(SCHEMA_SQL_PATH),
        "sqlite_database": str(DB_PATH),
    }

    for key, expected_path in expected.items():
        actual = source_files.get(key)
        if actual != expected_path:
            fail(f"source_files.{key} must be {expected_path!r}, got {actual!r}")


def validate_ddl_direction(data: dict[str, Any]) -> None:
    ddl_direction = data.get("ddl_direction")
    if not isinstance(ddl_direction, dict):
        fail("ddl_direction must be object")

    expected_true = [
        "add_only",
    ]
    expected_false = [
        "drop_table_allowed",
        "destructive_alter_allowed",
        "migration_execution_allowed_in_this_step",
        "schema_sql_write_allowed_in_this_step",
        "sqlite_write_allowed_in_this_step",
    ]

    for key in expected_true:
        if ddl_direction.get(key) is not True:
            fail(f"ddl_direction.{key} must be True, got {ddl_direction.get(key)!r}")

    for key in expected_false:
        if ddl_direction.get(key) is not False:
            fail(f"ddl_direction.{key} must be False, got {ddl_direction.get(key)!r}")

    if ddl_direction.get("future_candidate_statement") != "CREATE TABLE IF NOT EXISTS":
        fail(
            "ddl_direction.future_candidate_statement must be "
            "'CREATE TABLE IF NOT EXISTS'"
        )


def validate_canonical_keys(data: dict[str, Any]) -> None:
    canonical_keys = data.get("canonical_keys")
    if not isinstance(canonical_keys, dict):
        fail("canonical_keys must be object")

    race_key = canonical_keys.get("canonical_race_key")
    candidate_key = canonical_keys.get("canonical_candidate_key")

    if not isinstance(race_key, dict):
        fail("canonical_keys.canonical_race_key must be object")
    if not isinstance(candidate_key, dict):
        fail("canonical_keys.canonical_candidate_key must be object")

    if race_key.get("components") != ["race_date", "venue_id", "race_no"]:
        fail("canonical_race_key components mismatch")

    if candidate_key.get("components") != ["race_date", "venue_id", "race_no", "lane"]:
        fail("canonical_candidate_key components mismatch")

    not_pk = canonical_keys.get("not_primary_key_components")
    require_contains_all(
        not_pk,
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
        "canonical_keys.not_primary_key_components",
    )


def validate_ddl_preview_tables(data: dict[str, Any]) -> None:
    tables = data.get("ddl_preview_tables")
    if not isinstance(tables, list):
        fail("ddl_preview_tables must be list")

    if len(tables) != 8:
        fail(f"ddl_preview_tables must contain 8 items, got {len(tables)}")

    names = []
    for i, item in enumerate(tables):
        if not isinstance(item, dict):
            fail(f"ddl_preview_tables[{i}] must be object")

        table_name = item.get("table_name")
        names.append(table_name)

        if table_name not in REQUIRED_MINIMAL_TABLES:
            fail(f"ddl_preview_tables[{i}].table_name unexpected: {table_name!r}")

        role = item.get("role")
        if not isinstance(role, str) or not role.strip():
            fail(f"ddl_preview_tables[{i}].role must be non-empty string")

        primary_key = item.get("primary_key")
        if not isinstance(primary_key, list) or not primary_key:
            fail(f"ddl_preview_tables[{i}].primary_key must be non-empty list")

        candidate_columns = item.get("candidate_columns")
        if not isinstance(candidate_columns, list) or not candidate_columns:
            fail(f"ddl_preview_tables[{i}].candidate_columns must be non-empty list")

        ddl = item.get("candidate_ddl_preview")
        if not isinstance(ddl, str) or not ddl.strip():
            fail(f"ddl_preview_tables[{i}].candidate_ddl_preview must be non-empty string")

        ddl_upper = ddl.upper()
        if "CREATE TABLE IF NOT EXISTS" not in ddl_upper:
            fail(
                f"ddl_preview_tables[{i}].candidate_ddl_preview must contain "
                "CREATE TABLE IF NOT EXISTS"
            )

        if "DROP TABLE" in ddl_upper:
            fail(f"ddl_preview_tables[{i}].candidate_ddl_preview must not contain DROP TABLE")

        if "ALTER TABLE" in ddl_upper:
            fail(f"ddl_preview_tables[{i}].candidate_ddl_preview must not contain ALTER TABLE")

    if names != REQUIRED_MINIMAL_TABLES:
        fail(f"ddl_preview_tables order mismatch: {names!r}")


def validate_existing_history_policy(data: dict[str, Any]) -> None:
    policy = data.get("existing_history_tables_policy")
    if not isinstance(policy, dict):
        fail("existing_history_tables_policy must be object")

    if policy.get("policy") != "preserve":
        fail("existing_history_tables_policy.policy must be preserve")

    if policy.get("existing_history_tables_preserved") is not True:
        fail("existing_history_tables_preserved must be True")

    require_contains_all(
        policy.get("tables"),
        REQUIRED_HISTORY_TABLES,
        "existing_history_tables_policy.tables",
    )

    for key in ["drop_allowed", "recreate_allowed", "destructive_alter_allowed"]:
        if policy.get(key) is not False:
            fail(f"existing_history_tables_policy.{key} must be False")


def validate_pre_night_constraints(data: dict[str, Any]) -> None:
    constraints = data.get("pre_night_safety_constraints")
    if not isinstance(constraints, dict):
        fail("pre_night_safety_constraints must be object")

    if constraints.get("pre_night_only") is not True:
        fail("pre_night_safety_constraints.pre_night_only must be True")

    if constraints.get("results_and_payouts_allowed_as_pre_night_inputs") is not False:
        fail(
            "pre_night_safety_constraints."
            "results_and_payouts_allowed_as_pre_night_inputs must be False"
        )

    require_contains_all(
        constraints.get("forbidden_information"),
        REQUIRED_FORBIDDEN_INFORMATION,
        "pre_night_safety_constraints.forbidden_information",
    )


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
    ]:
        if state.get(key) is not False:
            fail(f"current_repository_state.{key} must be False")


def validate_safety_decisions(data: dict[str, Any]) -> None:
    safety = data.get("safety_decisions")
    if not isinstance(safety, dict):
        fail("safety_decisions must be object")

    required_true = [
        "do_not_modify_schema_sql_in_step152_b",
        "do_not_modify_sqlite_db_in_step152_b",
        "do_not_execute_create_table_in_step152_b",
        "do_not_execute_alter_table_in_step152_b",
        "do_not_execute_drop_table_in_step152_b",
        "do_not_run_migration_in_step152_b",
        "do_not_modify_prediction_json",
        "do_not_enable_history_features",
        "do_not_connect_prediction_core",
    ]

    for key in required_true:
        if safety.get(key) is not True:
            fail(f"safety_decisions.{key} must be True")


def main() -> None:
    require_file(CONFIG_PATH)
    require_file(PREDICTION_PATH)
    require_file(SCHEMA_SQL_PATH)
    require_file(DB_PATH)
    require_file(EXPORTER_PATH)
    require_file(PREVIEW_PATH)

    config = load_json(CONFIG_PATH)
    if bool(config.get("enabled", False)):
        fail("data/history_feature_config.json enabled must remain false")

    data = load_json(PREVIEW_PATH)

    require_equal(data, "step", "STEP152-B")
    require_equal(data, "preview_type", "phase1-mvp-db-schema-ddl-preview")
    require_equal(data, "connection_mode", "ddl-preview-only")
    require_true(data, "safe_mode")
    require_equal(data, "ddl_execution_mode", "not-executed")
    require_true(data, "ddl_preview_only")

    for key in REQUIRED_FALSE_FLAGS:
        require_false(data, key)

    require_equal(data, "minimal_table_count", 8)
    require_list_equal(data, "minimal_tables", REQUIRED_MINIMAL_TABLES)
    require_list_equal(data, "implementation_order", REQUIRED_IMPLEMENTATION_ORDER)

    output = data.get("output")
    if output != str(PREVIEW_PATH):
        fail(f"output must be {str(PREVIEW_PATH)!r}, got {output!r}")

    validate_source_files(data)
    validate_ddl_direction(data)
    validate_canonical_keys(data)
    validate_ddl_preview_tables(data)
    validate_existing_history_policy(data)
    validate_pre_night_constraints(data)
    validate_current_repository_state(data)
    validate_safety_decisions(data)

    require_not_modified(SCHEMA_SQL_PATH, "db/schema.sql")
    require_not_modified(DB_PATH, "db/boatrace.sqlite3")
    require_not_modified(PREDICTION_PATH, "docs/prediction.json")
    require_not_modified(CONFIG_PATH, "data/history_feature_config.json")

    schema_sql_currently_modified = git_diff_modified(SCHEMA_SQL_PATH)
    database_currently_modified = git_diff_modified(DB_PATH)
    prediction_json_currently_modified = git_diff_modified(PREDICTION_PATH)
    config_currently_modified = git_diff_modified(CONFIG_PATH)

    print("Phase 1 MVP DB schema DDL preview validation: OK")
    print("STEP 152-C CHECK: OK")
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
    print(f"minimal_table_count={data['minimal_table_count']}")
    print(f"ddl_execution_mode={data['ddl_execution_mode']}")
    print(f"ddl_preview_only={data['ddl_preview_only']}")
    print(f"schema_sql_currently_modified={schema_sql_currently_modified}")
    print(f"database_currently_modified={database_currently_modified}")
    print(f"prediction_json_currently_modified={prediction_json_currently_modified}")
    print(f"config_currently_modified={config_currently_modified}")


if __name__ == "__main__":
    main()
