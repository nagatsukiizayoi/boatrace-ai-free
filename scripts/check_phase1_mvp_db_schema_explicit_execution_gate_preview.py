#!/usr/bin/env python3
"""
STEP157-C: Validate Phase 1 MVP DB schema explicit execution gate preview.

This checker validates:
- docs/phase1_mvp_db_schema_explicit_execution_gate_preview.json

It does not execute migration, DDL, DB writes, schema writes, prediction writes,
config enablement, prediction core connection, or automatic betting.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


PREVIEW_JSON = Path("docs/phase1_mvp_db_schema_explicit_execution_gate_preview.json")
EXPORTER_SCRIPT = Path("scripts/export_phase1_mvp_db_schema_explicit_execution_gate_preview.py")

RUNTIME_GUARD_JSON = Path("docs/phase1_mvp_db_schema_runtime_guard_preview.json")
EXECUTION_PREVIEW_JSON = Path("docs/phase1_mvp_db_schema_migration_execution_preview.json")
MIGRATION_DRAFT_SCRIPT = Path("scripts/migrate_phase1_mvp_db_schema.py")

SCHEMA_SQL = Path("db/schema.sql")
SQLITE_DB = Path("db/boatrace.sqlite3")
PREDICTION_JSON = Path("docs/prediction.json")
CONFIG_JSON = Path("data/history_feature_config.json")

MINIMAL_TABLES = [
    "races",
    "entries",
    "feature_sets",
    "prediction_runs",
    "predictions",
    "results",
    "payouts",
    "stage_metrics",
]

FALSE_FLAGS = [
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

GATE_REQUIREMENTS_TRUE = [
    "explicit_execute_flag_required",
    "default_mode_must_remain_dry_run",
    "clean_git_status_required",
    "protected_file_hash_record_required",
    "sqlite_backup_required",
    "readiness_checks_required",
    "ddl_candidates_audit_required",
    "runtime_guard_preview_required",
    "execution_preview_required",
    "migration_draft_required",
    "create_table_if_not_exists_only",
    "destructive_sql_forbidden",
    "preserve_history_tables",
    "prediction_json_write_forbidden",
    "config_enablement_forbidden",
    "prediction_core_connection_forbidden",
    "automatic_betting_forbidden",
    "execution_must_be_separate_explicit_step",
    "fail_closed_on_missing_gate",
]

FAIL_CLOSED_TRUE = [
    "fail_closed_on_missing_gate",
    "fail_closed_on_dirty_git_status",
    "fail_closed_on_missing_backup",
    "fail_closed_on_missing_hash_record",
    "fail_closed_on_readiness_failure",
    "fail_closed_on_ddl_candidate_audit_failure",
    "fail_closed_on_destructive_sql",
    "fail_closed_on_missing_explicit_execute_flag",
    "fail_closed_on_non_dry_run_default",
]

ROLLBACK_TRUE = [
    "sqlite_backup_required",
    "restore_sqlite_backup",
    "git_restore_tracked_files",
    "record_git_status_before_execution",
    "record_commit_hash_before_execution",
    "record_schema_sql_hash_before_execution",
    "record_boatrace_sqlite_hash_before_execution",
    "record_prediction_json_hash_before_execution",
    "record_history_feature_config_hash_before_execution",
    "record_sqlite_table_list_before_execution",
    "record_sqlite_row_counts_before_execution",
    "readiness_checks_before_execution",
    "do_not_drop_history_races",
    "do_not_drop_history_results",
]

FORBIDDEN_SQL_PATTERNS = [
    "DROP TABLE",
    "DROP INDEX",
    "ALTER TABLE",
    "INSERT INTO",
    "UPDATE ",
    "DELETE FROM",
    "REPLACE INTO",
    "TRUNCATE",
]

PROTECTED_DIFF_FILES = [
    PREVIEW_JSON,
    EXPORTER_SCRIPT,
    RUNTIME_GUARD_JSON,
    EXECUTION_PREVIEW_JSON,
    MIGRATION_DRAFT_SCRIPT,
    SCHEMA_SQL,
    SQLITE_DB,
    PREDICTION_JSON,
    CONFIG_JSON,
]


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def require_file(path: Path) -> None:
    if not path.exists():
        fail(f"required file not found: {path}")


def load_json(path: Path) -> dict[str, Any]:
    require_file(path)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"failed to load JSON {path}: {exc}")
    raise AssertionError("unreachable")


def find_key(obj: Any, key: str) -> Any:
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for value in obj.values():
            found = find_key(value, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = find_key(item, key)
            if found is not None:
                return found
    return None


def require_value(data: Any, key: str, expected: Any) -> None:
    actual = find_key(data, key)
    if actual != expected:
        fail(f"{key} expected {expected!r}, got {actual!r}")


def require_nested_value(data: dict[str, Any], section: str, key: str, expected: Any) -> None:
    section_data = data.get(section)
    if not isinstance(section_data, dict):
        fail(f"{section} is missing or not an object")
    actual = section_data.get(key)
    if actual != expected:
        fail(f"{section}.{key} expected {expected!r}, got {actual!r}")


def git_modified(path: Path) -> bool:
    proc = subprocess.run(
        ["git", "--no-pager", "diff", "--quiet", "--", str(path)],
        text=True,
        capture_output=True,
    )
    if proc.returncode == 0:
        return False
    if proc.returncode == 1:
        return True
    fail(proc.stderr.strip() or f"git diff failed for {path}")
    raise AssertionError("unreachable")


def validate_metadata(data: dict[str, Any]) -> None:
    expected = {
        "step": "STEP157-B",
        "preview_type": "phase1-mvp-db-schema-explicit-execution-gate-preview",
        "connection_mode": "explicit-execution-gate-preview-only",
        "safe_mode": True,
        "explicit_execution_gate_preview_only": True,
        "migration_execution_mode": "not-executed",
        "ddl_execution_mode": "not-executed",
        "minimal_table_count": 8,
    }
    for key, value in expected.items():
        require_value(data, key, value)


def validate_false_flags(data: dict[str, Any]) -> None:
    for flag in FALSE_FLAGS:
        require_value(data, flag, False)


def validate_tables(data: dict[str, Any]) -> None:
    tables = data.get("minimal_tables")
    if tables != MINIMAL_TABLES:
        fail(f"minimal_tables expected {MINIMAL_TABLES!r}, got {tables!r}")


def validate_gate_requirements(data: dict[str, Any]) -> None:
    for key in GATE_REQUIREMENTS_TRUE:
        require_value(data, key, True)
        require_nested_value(data, "explicit_execution_gate_requirements", key, True)


def validate_fail_closed_policy(data: dict[str, Any]) -> None:
    for key in FAIL_CLOSED_TRUE:
        require_nested_value(data, "fail_closed_policy", key, True)


def validate_rollback_requirements(data: dict[str, Any]) -> None:
    for key in ROLLBACK_TRUE:
        require_nested_value(data, "rollback_requirements", key, True)


def validate_forbidden_sql_patterns(data: dict[str, Any]) -> None:
    patterns = data.get("forbidden_sql_patterns")
    if patterns != FORBIDDEN_SQL_PATTERNS:
        fail(f"forbidden_sql_patterns expected {FORBIDDEN_SQL_PATTERNS!r}, got {patterns!r}")


def validate_ddl_audit(data: dict[str, Any]) -> None:
    require_value(data, "ddl_candidates_table_count", 8)
    require_value(data, "ddl_candidates_danger_pattern_count", 0)

    audit = data.get("ddl_candidate_audit")
    if not isinstance(audit, dict):
        fail("ddl_candidate_audit missing or not object")

    if audit.get("ddl_candidates_table_count") != 8:
        fail("ddl_candidate_audit.ddl_candidates_table_count must be 8")
    if audit.get("ddl_candidates_danger_pattern_count") != 0:
        fail("ddl_candidate_audit.ddl_candidates_danger_pattern_count must be 0")
    if audit.get("ddl_candidates_tables") != MINIMAL_TABLES:
        fail("ddl_candidate_audit.ddl_candidates_tables mismatch")

    table_audits = audit.get("table_audits", [])
    if table_audits:
        if len(table_audits) != 8:
            fail("ddl_candidate_audit.table_audits length must be 8")
        for item in table_audits:
            if not item.get("has_create_table_if_not_exists"):
                fail(f"table audit missing CREATE TABLE IF NOT EXISTS: {item!r}")
            if item.get("danger_hits"):
                fail(f"table audit has danger hits: {item!r}")


def validate_references(data: dict[str, Any]) -> None:
    refs = data.get("references")
    if not isinstance(refs, dict):
        fail("references missing or not object")

    expected = {
        "runtime_guard_preview_json": "docs/phase1_mvp_db_schema_runtime_guard_preview.json",
        "runtime_guard_preview_step": "STEP156-B",
        "runtime_guard_checker": "STEP156-C",
        "execution_preview_json": "docs/phase1_mvp_db_schema_migration_execution_preview.json",
        "execution_preview_step": "STEP155-B",
        "migration_draft_script": "scripts/migrate_phase1_mvp_db_schema.py",
        "migration_draft_step": "STEP154-B",
        "migration_draft_checker": "STEP154-C",
    }

    for key, value in expected.items():
        actual = refs.get(key)
        if actual != value:
            fail(f"references.{key} expected {value!r}, got {actual!r}")


def validate_policies(data: dict[str, Any]) -> None:
    key_policy = data.get("key_policy")
    if not isinstance(key_policy, dict):
        fail("key_policy missing or not object")

    if key_policy.get("race_id_policy") != "race_id = canonical_race_key":
        fail("race_id_policy mismatch")
    if key_policy.get("canonical_candidate_key_policy") != 'canonical_candidate_key = race_id + "_" + lane':
        fail("canonical_candidate_key_policy mismatch")

    pdf = data.get("pdf_operation_constraints")
    if not isinstance(pdf, dict):
        fail("pdf_operation_constraints missing or not object")

    expected_pdf = {
        "no_automatic_betting": True,
        "collection_interval_policy": "5 to 15 minutes",
        "sqlite_commit_policy": "nightly SQLite merge",
        "llm_usage_policy": "LLM not used for normal prediction",
    }
    for key, value in expected_pdf.items():
        actual = pdf.get(key)
        if actual != value:
            fail(f"pdf_operation_constraints.{key} expected {value!r}, got {actual!r}")

    pre = data.get("pre_night_constraints")
    if not isinstance(pre, dict):
        fail("pre_night_constraints missing or not object")

    if pre.get("pre_night_only") is not True:
        fail("pre_night_only must be True")
    if pre.get("results_and_payouts_allowed_as_pre_night_inputs") is not False:
        fail("results_and_payouts_allowed_as_pre_night_inputs must be False")


def validate_safety_decision(data: dict[str, Any]) -> None:
    safety = data.get("safety_decision")
    if not isinstance(safety, dict):
        fail("safety_decision missing or not object")

    expected = {
        "status": "preview-only",
        "no_migration_execution": True,
        "no_ddl_execution": True,
        "no_database_write": True,
        "no_schema_sql_write": True,
        "no_prediction_json_write": True,
        "no_config_enablement": True,
        "no_prediction_core_connection": True,
        "no_automatic_betting": True,
        "future_execution_requires_separate_explicit_step": True,
    }

    for key, value in expected.items():
        actual = safety.get(key)
        if actual != value:
            fail(f"safety_decision.{key} expected {value!r}, got {actual!r}")


def validate_required_files() -> None:
    for path in [
        PREVIEW_JSON,
        EXPORTER_SCRIPT,
        RUNTIME_GUARD_JSON,
        EXECUTION_PREVIEW_JSON,
        MIGRATION_DRAFT_SCRIPT,
        SCHEMA_SQL,
        SQLITE_DB,
        PREDICTION_JSON,
        CONFIG_JSON,
    ]:
        require_file(path)


def validate_protected_file_diffs() -> dict[str, bool]:
    states: dict[str, bool] = {}
    for path in PROTECTED_DIFF_FILES:
        require_file(path)
        states[str(path)] = git_modified(path)
    return states


def main() -> None:
    validate_required_files()

    data = load_json(PREVIEW_JSON)

    validate_metadata(data)
    validate_false_flags(data)
    validate_tables(data)
    validate_gate_requirements(data)
    validate_fail_closed_policy(data)
    validate_rollback_requirements(data)
    validate_forbidden_sql_patterns(data)
    validate_ddl_audit(data)
    validate_references(data)
    validate_policies(data)
    validate_safety_decision(data)

    modified = validate_protected_file_diffs()

    if modified[str(SCHEMA_SQL)]:
        fail("db/schema.sql has uncommitted diff")
    if modified[str(SQLITE_DB)]:
        fail("db/boatrace.sqlite3 has uncommitted diff")
    if modified[str(PREDICTION_JSON)]:
        fail("docs/prediction.json has uncommitted diff")
    if modified[str(CONFIG_JSON)]:
        fail("data/history_feature_config.json has uncommitted diff")
    if modified[str(PREVIEW_JSON)]:
        fail("explicit execution gate preview JSON has uncommitted diff")
    if modified[str(EXPORTER_SCRIPT)]:
        fail("explicit execution gate preview exporter has uncommitted diff")

    print("Phase 1 MVP DB schema explicit execution gate preview validation: OK")
    print("STEP 157-C CHECK: OK")
    print(f"preview_type={data['preview_type']}")
    print(f"connection_mode={data['connection_mode']}")
    print(f"explicit_execution_gate_preview_only={data['explicit_execution_gate_preview_only']}")
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
    print(f"explicit_execute_flag_required={data['explicit_execute_flag_required']}")
    print(f"default_mode_must_remain_dry_run={data['default_mode_must_remain_dry_run']}")
    print(f"fail_closed_on_missing_gate={data['fail_closed_on_missing_gate']}")
    print(f"runtime_guard_preview_required={data['runtime_guard_preview_required']}")
    print(f"ddl_candidates_table_count={data['ddl_candidates_table_count']}")
    print(f"ddl_candidates_danger_pattern_count={data['ddl_candidates_danger_pattern_count']}")
    print(f"race_id_policy={data['key_policy']['race_id_policy']}")
    print(f"canonical_candidate_key_policy={data['key_policy']['canonical_candidate_key_policy']}")
    print(f"no_automatic_betting={data['pdf_operation_constraints']['no_automatic_betting']}")
    print(f"collection_interval_policy={data['pdf_operation_constraints']['collection_interval_policy']}")
    print(f"sqlite_commit_policy={data['pdf_operation_constraints']['sqlite_commit_policy']}")
    print(f"llm_usage_policy={data['pdf_operation_constraints']['llm_usage_policy']}")
    print(f"pre_night_only={data['pre_night_constraints']['pre_night_only']}")
    print(f"results_and_payouts_allowed_as_pre_night_inputs={data['pre_night_constraints']['results_and_payouts_allowed_as_pre_night_inputs']}")
    print(f"schema_sql_currently_modified={modified[str(SCHEMA_SQL)]}")
    print(f"database_currently_modified={modified[str(SQLITE_DB)]}")
    print(f"prediction_json_currently_modified={modified[str(PREDICTION_JSON)]}")
    print(f"config_currently_modified={modified[str(CONFIG_JSON)]}")
    print(f"explicit_execution_gate_preview_currently_modified={modified[str(PREVIEW_JSON)]}")


if __name__ == "__main__":
    main()
