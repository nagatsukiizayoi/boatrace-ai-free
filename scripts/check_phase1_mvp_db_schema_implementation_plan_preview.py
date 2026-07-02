from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


CONFIG_PATH = Path("data/history_feature_config.json")
PREDICTION_PATH = Path("docs/prediction.json")
SCHEMA_SQL_PATH = Path("db/schema.sql")
DB_PATH = Path("db/boatrace.sqlite3")
EXPORTER_PATH = Path("scripts/export_phase1_mvp_db_schema_implementation_plan_preview.py")
SCHEMA_PREVIEW_PATH = Path("docs/phase1_mvp_db_schema_preview.json")
PREVIEW_PATH = Path("docs/phase1_mvp_db_schema_implementation_plan_preview.json")


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


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    sys.exit(1)


def load_json(path: Path) -> Any:
    if not path.exists():
        fail(f"missing file: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON: {path}: {exc}")


def require_key(data: dict[str, Any], key: str) -> Any:
    if key not in data:
        fail(f"missing required key: {key}")
    return data[key]


def require_value(data: dict[str, Any], key: str, expected: Any) -> Any:
    value = require_key(data, key)
    if value != expected:
        fail(f"{key} must be {expected!r}, got {value!r}")
    return value


def require_false(data: dict[str, Any], key: str) -> None:
    value = require_key(data, key)
    if value is not False:
        fail(f"{key} must be False, got {value!r}")


def require_true(data: dict[str, Any], key: str) -> None:
    value = require_key(data, key)
    if value is not True:
        fail(f"{key} must be True, got {value!r}")


def require_dict(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = require_key(data, key)
    if not isinstance(value, dict):
        fail(f"{key} must be dict, got {type(value).__name__}")
    return value


def require_list(data: dict[str, Any], key: str) -> list[Any]:
    value = require_key(data, key)
    if not isinstance(value, list):
        fail(f"{key} must be list, got {type(value).__name__}")
    return value


def require_nonnegative_int(data: dict[str, Any], key: str) -> int:
    value = require_key(data, key)
    if not isinstance(value, int) or value < 0:
        fail(f"{key} must be non-negative int, got {value!r}")
    return value


def check_no_diff(path: Path, label: str) -> None:
    if not path.exists():
        fail(f"missing file for diff check: {path}")

    result = subprocess.run(
        ["git", "diff", "--quiet", "--", str(path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode == 1:
        fail(f"{label} has uncommitted diff: {path}")

    if result.returncode not in (0, 1):
        fail(f"git diff check failed for {path}: {result.stderr.strip()}")


def require_name_list(actual: list[Any], expected: list[str], label: str) -> None:
    if actual != expected:
        fail(f"{label} must be {expected!r}, got {actual!r}")


def require_contains_all(values: list[Any], expected: list[str], label: str) -> None:
    if not all(isinstance(item, str) for item in values):
        fail(f"{label} must contain only strings")

    missing = [item for item in expected if item not in values]
    if missing:
        fail(f"{label} missing required items: {missing}")


def main() -> None:
    if not EXPORTER_PATH.exists():
        fail(f"missing exporter script: {EXPORTER_PATH}")

    config = load_json(CONFIG_PATH)
    schema_preview = load_json(SCHEMA_PREVIEW_PATH)
    preview = load_json(PREVIEW_PATH)

    if not isinstance(config, dict):
        fail(f"{CONFIG_PATH} must contain JSON object")

    if not isinstance(schema_preview, dict):
        fail(f"{SCHEMA_PREVIEW_PATH} must contain JSON object")

    if not isinstance(preview, dict):
        fail(f"{PREVIEW_PATH} must contain JSON object")

    if config.get("enabled") is not False:
        fail(f"data/history_feature_config.json enabled must be False, got {config.get('enabled')!r}")

    require_value(schema_preview, "step", "STEP150-B")
    require_value(schema_preview, "preview_type", "phase1-mvp-db-schema")
    require_value(schema_preview, "connection_mode", "design-only")

    require_value(preview, "step", "STEP151-B")
    require_value(preview, "preview_type", "phase1-mvp-db-schema-implementation-plan")
    require_value(preview, "connection_mode", "planning-only")

    require_true(preview, "safe_mode")
    require_false(preview, "config_enabled")
    require_false(preview, "history_features_enabled")
    require_false(preview, "prediction_core_connected")
    require_false(preview, "affects_prediction_output")
    require_false(preview, "modifies_prediction_json")
    require_false(preview, "writes_prediction_json")
    require_false(preview, "writes_schema_sql")
    require_false(preview, "writes_database")
    require_false(preview, "creates_tables")
    require_false(preview, "alters_tables")
    require_false(preview, "runs_migration")

    require_false(preview, "schema_sql_currently_modified")
    require_false(preview, "database_currently_modified")
    require_false(preview, "prediction_json_currently_modified")

    source_files = require_dict(preview, "source_files")
    expected_source_files = {
        "history_feature_config": str(CONFIG_PATH),
        "prediction_json": str(PREDICTION_PATH),
        "schema_sql": str(SCHEMA_SQL_PATH),
        "database": str(DB_PATH),
        "phase1_mvp_db_schema_preview": str(SCHEMA_PREVIEW_PATH),
    }

    for key, expected in expected_source_files.items():
        actual = source_files.get(key)
        if actual != expected:
            fail(f"source_files.{key} must be {expected!r}, got {actual!r}")

    output_file = require_key(preview, "output_file")
    if output_file != str(PREVIEW_PATH):
        fail(f"output_file must be {str(PREVIEW_PATH)!r}, got {output_file!r}")

    schema_sql_inspection = require_dict(preview, "schema_sql_inspection")
    if schema_sql_inspection.get("schema_sql_path") != str(SCHEMA_SQL_PATH):
        fail("schema_sql_inspection.schema_sql_path mismatch")

    database_inspection = require_dict(preview, "database_inspection")
    if database_inspection.get("db_path") != str(DB_PATH):
        fail("database_inspection.db_path mismatch")

    if database_inspection.get("history_results_exists") is not True:
        fail("database_inspection.history_results_exists must be True")

    if database_inspection.get("history_races_exists") is not True:
        fail("database_inspection.history_races_exists must be True")

    phase1_presence = database_inspection.get("phase1_table_presence")
    if not isinstance(phase1_presence, dict):
        fail("database_inspection.phase1_table_presence must be dict")

    for table in REQUIRED_MINIMAL_TABLES:
        if table not in phase1_presence:
            fail(f"database_inspection.phase1_table_presence missing {table}")

    minimal_tables = require_list(preview, "minimal_tables")
    require_name_list(minimal_tables, REQUIRED_MINIMAL_TABLES, "minimal_tables")

    minimal_count = require_nonnegative_int(preview, "minimal_table_count")
    if minimal_count != len(REQUIRED_MINIMAL_TABLES):
        fail(f"minimal_table_count must be {len(REQUIRED_MINIMAL_TABLES)}, got {minimal_count}")

    implementation_order = require_list(preview, "implementation_order")
    require_name_list(implementation_order, REQUIRED_MINIMAL_TABLES, "implementation_order")

    implementation_order_reason = require_list(preview, "implementation_order_reason")
    if len(implementation_order_reason) == 0:
        fail("implementation_order_reason must not be empty")

    canonical = require_dict(preview, "canonical_keys")

    race_key = require_dict(canonical, "canonical_race_key")
    race_components = require_list(race_key, "components")
    if race_components != ["race_date", "venue_id", "race_no"]:
        fail(f"canonical_race_key.components mismatch: {race_components!r}")

    candidate_key = require_dict(canonical, "canonical_candidate_key")
    candidate_components = require_list(candidate_key, "components")
    if candidate_components != ["race_date", "venue_id", "race_no", "lane"]:
        fail(f"canonical_candidate_key.components mismatch: {candidate_components!r}")

    history_policy = require_dict(preview, "existing_history_tables_policy")
    require_true(history_policy, "preserve_history_results")
    require_true(history_policy, "preserve_history_races")
    require_true(history_policy, "do_not_remove_existing_history_tables")

    implementation_policy = require_dict(preview, "schema_implementation_policy")
    require_true(implementation_policy, "preview_before_schema_sql_change")
    require_true(implementation_policy, "checker_before_database_change")
    require_true(implementation_policy, "rollback_policy_required_before_migration")
    require_true(implementation_policy, "schema_sql_changes_should_be_isolated")
    require_true(implementation_policy, "database_changes_should_be_isolated")
    require_true(implementation_policy, "no_prediction_output_change_during_schema_implementation")

    rollback = require_dict(preview, "rollback_policy")
    require_true(rollback, "record_schema_sql_hash_before_change")
    require_true(rollback, "record_database_hash_before_change")
    require_true(rollback, "do_not_blindly_delete_database")
    require_true(rollback, "if_history_tables_missing_rebuild_only_when_instructed")

    if rollback.get("restore_schema_sql_command") != "git restore db/schema.sql":
        fail("rollback_policy.restore_schema_sql_command mismatch")

    if rollback.get("restore_prediction_json_command") != "git restore docs/prediction.json":
        fail("rollback_policy.restore_prediction_json_command mismatch")

    constraints = require_list(preview, "pre_night_safety_constraints")
    require_contains_all(
        constraints,
        [
            "PRE_NIGHT must not use same-day odds",
            "PRE_NIGHT must not use exhibition_time",
            "PRE_NIGHT must not use exhibition_st",
            "PRE_NIGHT must not use exhibition_course",
            "PRE_NIGHT must not use results as features",
            "PRE_NIGHT must not use payouts as features",
        ],
        "pre_night_safety_constraints",
    )

    future_steps = require_list(preview, "future_schema_implementation_steps")
    if len(future_steps) == 0:
        fail("future_schema_implementation_steps must not be empty")

    safety = require_dict(preview, "safety_decision")
    require_true(safety, "do_not_enable_history_features")
    require_true(safety, "do_not_connect_prediction_core")
    require_true(safety, "do_not_modify_prediction_json")
    require_true(safety, "do_not_modify_schema_sql_in_step151b")
    require_true(safety, "do_not_modify_database_in_step151b")
    require_true(safety, "do_not_create_tables_in_step151b")
    require_true(safety, "do_not_run_migration_in_step151b")
    require_true(safety, "do_not_change_prediction_scores")
    require_true(safety, "do_not_change_ranks")
    require_true(safety, "do_not_change_recommendations")
    require_true(safety, "do_not_change_expected_values")

    next_step = require_dict(preview, "next_step")
    if next_step.get("step") != "STEP151-C":
        fail(f"next_step.step must be STEP151-C, got {next_step.get('step')!r}")

    check_no_diff(PREDICTION_PATH, "docs/prediction.json")
    check_no_diff(SCHEMA_SQL_PATH, "db/schema.sql")
    check_no_diff(DB_PATH, "db/boatrace.sqlite3")

    print("Phase 1 MVP DB schema implementation plan preview validation: OK")
    print("STEP 151-C CHECK: OK")
    print(f"output={PREVIEW_PATH}")
    print("preview_type=phase1-mvp-db-schema-implementation-plan")
    print("connection_mode=planning-only")
    print("config_enabled=False")
    print("history_features_enabled=False")
    print("prediction_core_connected=False")
    print("modifies_prediction_json=False")
    print("writes_prediction_json=False")
    print("writes_schema_sql=False")
    print("writes_database=False")
    print("creates_tables=False")
    print("alters_tables=False")
    print("runs_migration=False")
    print(f"minimal_table_count={minimal_count}")
    print("implementation_order=" + ",".join(REQUIRED_MINIMAL_TABLES))
    print("schema_sql_currently_modified=False")
    print("database_currently_modified=False")
    print("prediction_json_currently_modified=False")


if __name__ == "__main__":
    main()
