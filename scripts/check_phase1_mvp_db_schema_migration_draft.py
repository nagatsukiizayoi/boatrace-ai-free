#!/usr/bin/env python3
"""
STEP154-C: Validate Phase 1 MVP DB schema migration draft.

This checker validates:
- scripts/migrate_phase1_mvp_db_schema.py

It verifies that the draft migration script is dry-run only and does not execute DDL,
does not write DB/schema/prediction/config files, and keeps Phase 1 MVP safety policy.

This checker must not modify:
- db/schema.sql
- db/boatrace.sqlite3
- docs/prediction.json
- data/history_feature_config.json
- docs/phase1_mvp_db_schema_migration_script_preview.json
- docs/phase1_mvp_db_schema_ddl_preview.json
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


DRAFT_SCRIPT_PATH = Path("scripts/migrate_phase1_mvp_db_schema.py")
CONFIG_PATH = Path("data/history_feature_config.json")
PREDICTION_PATH = Path("docs/prediction.json")
SCHEMA_SQL_PATH = Path("db/schema.sql")
DB_PATH = Path("db/boatrace.sqlite3")
MIGRATION_PREVIEW_PATH = Path("docs/phase1_mvp_db_schema_migration_script_preview.json")
DDL_PREVIEW_PATH = Path("docs/phase1_mvp_db_schema_ddl_preview.json")

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

DANGER_PATTERNS = [
    "DROP TABLE",
    "DROP INDEX",
    "ALTER TABLE",
    "DELETE FROM",
    "UPDATE ",
    "INSERT INTO",
    "REPLACE INTO",
    "TRUNCATE",
]

REQUIRED_DRAFT_OUTPUT_LINES = [
    "Phase 1 MVP DB schema migration draft: OK",
    "STEP 154-B CHECK: OK",
    "mode=dry-run",
    "executes_ddl=False",
    "writes_database=False",
    "writes_schema_sql=False",
    "creates_tables=False",
    "alters_tables=False",
    "drops_tables=False",
    "runs_migration=False",
    "minimal_table_count=8",
    "danger_pattern_count=0",
    "danger_patterns=NONE",
]

PROTECTED_DIFF_PATHS = [
    SCHEMA_SQL_PATH,
    DB_PATH,
    PREDICTION_PATH,
    CONFIG_PATH,
    MIGRATION_PREVIEW_PATH,
    DDL_PREVIEW_PATH,
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


def recursive_find_key(obj: Any, key: str) -> Any:
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for value in obj.values():
            found = recursive_find_key(value, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = recursive_find_key(value, key)
            if found is not None:
                return found
    return None


def require_recursive_value(data: dict[str, Any], key: str, expected: Any) -> None:
    actual = recursive_find_key(data, key)
    if actual != expected:
        fail(f"{key} must be {expected!r}, got {actual!r}")


def require_recursive_truthy_value(data: dict[str, Any], key: str, expected: Any) -> None:
    actual = recursive_find_key(data, key)
    if actual != expected:
        fail(f"{key} must be {expected!r}, got {actual!r}")


def extract_assignment_from_ast(script_path: Path, name: str) -> Any:
    source = script_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(script_path))
    except SyntaxError as exc:
        fail(f"syntax error in {script_path}: {exc}")

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    try:
                        return ast.literal_eval(node.value)
                    except Exception as exc:
                        fail(f"could not literal_eval {name} in {script_path}: {exc}")

    fail(f"{name} assignment not found in {script_path}")
    return None


def validate_ddl_candidates() -> tuple[int, int]:
    ddl_candidates = extract_assignment_from_ast(DRAFT_SCRIPT_PATH, "DDL_CANDIDATES")

    if not isinstance(ddl_candidates, dict):
        fail("DDL_CANDIDATES must be a dict")

    actual_tables = list(ddl_candidates.keys())
    if actual_tables != REQUIRED_MINIMAL_TABLES:
        fail(f"DDL_CANDIDATES table order must be {REQUIRED_MINIMAL_TABLES!r}, got {actual_tables!r}")

    danger_hits: list[tuple[str, list[str]]] = []

    for table_name in REQUIRED_MINIMAL_TABLES:
        ddl = ddl_candidates.get(table_name)
        if not isinstance(ddl, str):
            fail(f"DDL_CANDIDATES[{table_name!r}] must be a string")

        ddl_upper = ddl.upper()

        if "CREATE TABLE IF NOT EXISTS" not in ddl_upper:
            fail(f"{table_name} DDL must contain CREATE TABLE IF NOT EXISTS")

        hits = [pattern for pattern in DANGER_PATTERNS if pattern in ddl_upper]
        if hits:
            danger_hits.append((table_name, hits))

    if danger_hits:
        fail(f"danger patterns found in DDL_CANDIDATES: {danger_hits!r}")

    return len(ddl_candidates), len(danger_hits)


def run_draft_script() -> str:
    result = subprocess.run(
        [sys.executable, str(DRAFT_SCRIPT_PATH)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )

    output = result.stdout

    if result.returncode != 0:
        fail(f"draft script returned non-zero exit code {result.returncode}\n{output}")

    for required in REQUIRED_DRAFT_OUTPUT_LINES:
        if required not in output:
            fail(f"draft script output missing required line: {required!r}")

    error_markers = ["Traceback", "PermissionError", "TypeError", "FAILED", "ERROR:"]
    for marker in error_markers:
        if marker in output:
            fail(f"draft script output contains error marker {marker!r}")

    return output


def validate_config() -> None:
    config = load_json(CONFIG_PATH)
    if bool(config.get("enabled", False)):
        fail("data/history_feature_config.json enabled must remain false")


def validate_migration_preview() -> dict[str, Any]:
    data = load_json(MIGRATION_PREVIEW_PATH)

    require_equal(data, "step", "STEP153-B")
    require_equal(data, "preview_type", "phase1-mvp-db-schema-migration-script-preview")
    require_equal(data, "connection_mode", "migration-preview-only")
    require_true(data, "safe_mode")
    require_true(data, "migration_script_preview_only")
    require_equal(data, "migration_script_execution_mode", "not-created-not-executed")
    require_equal(data, "ddl_execution_mode", "not-executed")
    require_equal(data, "minimal_table_count", 8)

    minimal_tables = data.get("minimal_tables")
    if minimal_tables != REQUIRED_MINIMAL_TABLES:
        fail(f"minimal_tables must be {REQUIRED_MINIMAL_TABLES!r}, got {minimal_tables!r}")

    implementation_order = data.get("implementation_order")
    if implementation_order != REQUIRED_MINIMAL_TABLES:
        fail(f"implementation_order must be {REQUIRED_MINIMAL_TABLES!r}, got {implementation_order!r}")

    for flag in REQUIRED_FALSE_FLAGS:
        require_false(data, flag)

    race_id_policy = recursive_find_key(data, "race_id_policy")
    if race_id_policy != "race_id = canonical_race_key":
        fail(f"race_id_policy must be 'race_id = canonical_race_key', got {race_id_policy!r}")

    canonical_candidate_key_policy = recursive_find_key(data, "canonical_candidate_key_policy")
    allowed_candidate_key_values = {
        'canonical_candidate_key = race_id + "_" + lane',
        "canonical_candidate_key = race_id + '_' + lane",
    }
    if canonical_candidate_key_policy not in allowed_candidate_key_values:
        fail(
            "canonical_candidate_key_policy must be "
            "'canonical_candidate_key = race_id + \"_\" + lane', "
            f"got {canonical_candidate_key_policy!r}"
        )

    require_recursive_truthy_value(data, "no_automatic_betting", True)
    require_recursive_value(data, "collection_interval_policy", "5 to 15 minutes")
    require_recursive_value(data, "sqlite_commit_policy", "nightly SQLite merge")
    require_recursive_value(data, "llm_usage_policy", "LLM not used for normal prediction")

    deferred_tables = recursive_find_key(data, "deferred_final_design_tables")
    required_deferred = [
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
    if not isinstance(deferred_tables, list):
        fail("deferred_final_design_tables must be a list")
    missing = [table for table in required_deferred if table not in deferred_tables]
    if missing:
        fail(f"deferred_final_design_tables missing required values: {missing!r}")

    pre_night_only = recursive_find_key(data, "pre_night_only")
    if pre_night_only is not True:
        fail(f"pre_night_only must be True, got {pre_night_only!r}")

    results_allowed = recursive_find_key(data, "results_and_payouts_allowed_as_pre_night_inputs")
    if results_allowed is not False:
        fail(
            "results_and_payouts_allowed_as_pre_night_inputs must be False, "
            f"got {results_allowed!r}"
        )

    return data


def validate_ddl_preview() -> dict[str, Any]:
    data = load_json(DDL_PREVIEW_PATH)

    require_equal(data, "step", "STEP152-B")
    require_equal(data, "preview_type", "phase1-mvp-db-schema-ddl-preview")
    require_equal(data, "connection_mode", "ddl-preview-only")
    require_true(data, "safe_mode")
    require_equal(data, "ddl_execution_mode", "not-executed")
    require_true(data, "ddl_preview_only")
    require_equal(data, "minimal_table_count", 8)

    minimal_tables = data.get("minimal_tables")
    if minimal_tables != REQUIRED_MINIMAL_TABLES:
        fail(f"DDL preview minimal_tables must be {REQUIRED_MINIMAL_TABLES!r}, got {minimal_tables!r}")

    for flag in [
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
    ]:
        require_false(data, flag)

    return data


def validate_protected_files_clean() -> dict[str, bool]:
    states: dict[str, bool] = {}
    for path in PROTECTED_DIFF_PATHS:
        require_file(path)
        modified = git_diff_modified(path)
        states[str(path)] = modified
        if modified:
            fail(f"protected file has uncommitted diff: {path}")
    return states


def main() -> None:
    for path in [
        DRAFT_SCRIPT_PATH,
        CONFIG_PATH,
        PREDICTION_PATH,
        SCHEMA_SQL_PATH,
        DB_PATH,
        MIGRATION_PREVIEW_PATH,
        DDL_PREVIEW_PATH,
    ]:
        require_file(path)

    validate_config()
    migration_preview = validate_migration_preview()
    validate_ddl_preview()

    table_count, danger_pattern_count = validate_ddl_candidates()
    if table_count != 8:
        fail(f"DDL_CANDIDATES table_count must be 8, got {table_count}")
    if danger_pattern_count != 0:
        fail(f"danger_pattern_count must be 0, got {danger_pattern_count}")

    run_draft_script()

    clean_states = validate_protected_files_clean()

    schema_sql_modified = clean_states[str(SCHEMA_SQL_PATH)]
    database_modified = clean_states[str(DB_PATH)]
    prediction_json_modified = clean_states[str(PREDICTION_PATH)]
    config_modified = clean_states[str(CONFIG_PATH)]
    migration_preview_modified = clean_states[str(MIGRATION_PREVIEW_PATH)]
    ddl_preview_modified = clean_states[str(DDL_PREVIEW_PATH)]

    race_id_policy = recursive_find_key(migration_preview, "race_id_policy")
    canonical_candidate_key_policy = recursive_find_key(
        migration_preview,
        "canonical_candidate_key_policy",
    )
    if canonical_candidate_key_policy == "canonical_candidate_key = race_id + '_' + lane":
        canonical_candidate_key_policy_for_print = 'canonical_candidate_key = race_id + "_" + lane'
    else:
        canonical_candidate_key_policy_for_print = canonical_candidate_key_policy

    print("Phase 1 MVP DB schema migration draft validation: OK")
    print("STEP 154-C CHECK: OK")
    print("mode=dry-run")
    print("executes_ddl=False")
    print("writes_database=False")
    print("writes_schema_sql=False")
    print("creates_tables=False")
    print("alters_tables=False")
    print("drops_tables=False")
    print("runs_migration=False")
    print("minimal_table_count=8")
    print("danger_pattern_count=0")
    print("danger_patterns=NONE")
    print(f"race_id_policy={race_id_policy}")
    print(f"canonical_candidate_key_policy={canonical_candidate_key_policy_for_print}")
    print("no_automatic_betting=True")
    print("collection_interval_policy=5 to 15 minutes")
    print("sqlite_commit_policy=nightly SQLite merge")
    print("llm_usage_policy=LLM not used for normal prediction")
    print(f"schema_sql_currently_modified={schema_sql_modified}")
    print(f"database_currently_modified={database_modified}")
    print(f"prediction_json_currently_modified={prediction_json_modified}")
    print(f"config_currently_modified={config_modified}")
    print(f"migration_preview_currently_modified={migration_preview_modified}")
    print(f"ddl_preview_currently_modified={ddl_preview_modified}")


if __name__ == "__main__":
    main()
