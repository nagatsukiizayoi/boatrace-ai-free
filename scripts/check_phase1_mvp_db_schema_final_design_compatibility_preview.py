#!/usr/bin/env python3
"""
STEP158-C: Validate Phase 1 MVP DB schema final design compatibility preview.

This checker validates:
- docs/phase1_mvp_db_schema_final_design_compatibility_preview.json

It does not execute migration, DDL, DB writes, schema writes, prediction writes,
config enablement, prediction core connection, or automatic betting.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


PREVIEW_JSON = Path("docs/phase1_mvp_db_schema_final_design_compatibility_preview.json")
EXPORTER_SCRIPT = Path("scripts/export_phase1_mvp_db_schema_final_design_compatibility_preview.py")

EXPLICIT_GATE_JSON = Path("docs/phase1_mvp_db_schema_explicit_execution_gate_preview.json")
EXPLICIT_GATE_EXPORTER = Path("scripts/export_phase1_mvp_db_schema_explicit_execution_gate_preview.py")
EXPLICIT_GATE_CHECKER = Path("scripts/check_phase1_mvp_db_schema_explicit_execution_gate_preview.py")

RUNTIME_GUARD_JSON = Path("docs/phase1_mvp_db_schema_runtime_guard_preview.json")
EXECUTION_PREVIEW_JSON = Path("docs/phase1_mvp_db_schema_migration_execution_preview.json")
MIGRATION_DRAFT_SCRIPT = Path("scripts/migrate_phase1_mvp_db_schema.py")

SCHEMA_SQL = Path("db/schema.sql")
SQLITE_DB = Path("db/boatrace.sqlite3")
PREDICTION_JSON = Path("docs/prediction.json")
CONFIG_JSON = Path("data/history_feature_config.json")

PHASE1_MVP_TABLES = [
    "races",
    "entries",
    "feature_sets",
    "prediction_runs",
    "predictions",
    "results",
    "payouts",
    "stage_metrics",
]

FINAL_DESIGN_TABLES = [
    "races",
    "entries",
    "racer_stats_snapshot",
    "motor_boat_stats_snapshot",
    "venue_bias_daily",
    "weather_water_snapshots",
    "exhibition_snapshots",
    "odds_snapshots",
    "ingestion_runs",
    "feature_sets",
    "prediction_runs",
    "predictions",
    "prediction_changes",
    "results",
    "payouts",
    "stage_metrics",
    "stage_transition_metrics",
    "model_registry",
    "training_runs",
]

DEFERRED_TABLES = [
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

COMPATIBILITY_TRUE = [
    "phase1_is_safe_subset_of_final_design",
    "phase1_mvp_is_pre_night_first",
    "live_update_tables_deferred",
    "odds_exhibition_weather_tables_deferred",
    "model_training_tables_deferred",
    "stage_transition_tables_deferred",
    "future_phases_required_for_full_design",
]

PRE_NIGHT_EXPECTED = {
    "pre_night_only": True,
    "same_day_odds_allowed": False,
    "final_odds_allowed": False,
    "exhibition_data_allowed": False,
    "same_day_weather_after_cutoff_allowed": False,
    "confirmed_outcomes_allowed": False,
    "results_and_payouts_allowed_as_pre_night_inputs": False,
}

PDF_EXPECTED = {
    "no_automatic_betting": True,
    "collection_interval_policy": "5 to 15 minutes",
    "sqlite_commit_policy": "nightly SQLite merge",
    "llm_usage_policy": "LLM not used for normal prediction",
    "smartphone_centric_operation": True,
}

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
    EXPLICIT_GATE_JSON,
    EXPLICIT_GATE_EXPORTER,
    EXPLICIT_GATE_CHECKER,
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
        fail(f"{section} missing or not object")
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


def validate_required_files() -> None:
    for path in [
        PREVIEW_JSON,
        EXPORTER_SCRIPT,
        EXPLICIT_GATE_JSON,
        EXPLICIT_GATE_EXPORTER,
        EXPLICIT_GATE_CHECKER,
        RUNTIME_GUARD_JSON,
        EXECUTION_PREVIEW_JSON,
        MIGRATION_DRAFT_SCRIPT,
        SCHEMA_SQL,
        SQLITE_DB,
        PREDICTION_JSON,
        CONFIG_JSON,
    ]:
        require_file(path)


def validate_metadata(data: dict[str, Any]) -> None:
    expected = {
        "step": "STEP158-B",
        "preview_type": "phase1-mvp-db-schema-final-design-compatibility-preview",
        "connection_mode": "final-design-compatibility-preview-only",
        "safe_mode": True,
        "final_design_compatibility_preview_only": True,
        "migration_execution_mode": "not-executed",
        "ddl_execution_mode": "not-executed",
        "minimal_table_count": 8,
        "final_design_table_count": 19,
        "deferred_table_count": 11,
    }
    for key, value in expected.items():
        require_value(data, key, value)


def validate_false_flags(data: dict[str, Any]) -> None:
    for flag in FALSE_FLAGS:
        require_value(data, flag, False)


def validate_tables(data: dict[str, Any]) -> None:
    if data.get("minimal_tables") != PHASE1_MVP_TABLES:
        fail(f"minimal_tables mismatch: {data.get('minimal_tables')!r}")

    if data.get("final_design_tables") != FINAL_DESIGN_TABLES:
        fail(f"final_design_tables mismatch: {data.get('final_design_tables')!r}")

    if data.get("deferred_tables") != DEFERRED_TABLES:
        fail(f"deferred_tables mismatch: {data.get('deferred_tables')!r}")

    for table in PHASE1_MVP_TABLES:
        if table not in FINAL_DESIGN_TABLES:
            fail(f"Phase 1 MVP table not in final design tables: {table}")

    overlap = set(PHASE1_MVP_TABLES).intersection(DEFERRED_TABLES)
    if overlap:
        fail(f"Phase 1 MVP tables must not be deferred: {sorted(overlap)!r}")


def validate_compatibility_decisions(data: dict[str, Any]) -> None:
    for key in COMPATIBILITY_TRUE:
        require_value(data, key, True)
        require_nested_value(data, "compatibility_decisions", key, True)


def validate_pre_night_constraints(data: dict[str, Any]) -> None:
    for key, expected in PRE_NIGHT_EXPECTED.items():
        require_value(data, key, expected)
        require_nested_value(data, "pre_night_constraints", key, expected)


def validate_pdf_operation_constraints(data: dict[str, Any]) -> None:
    for key, expected in PDF_EXPECTED.items():
        require_value(data, key, expected)
        require_nested_value(data, "pdf_operation_constraints", key, expected)


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
    if audit.get("ddl_candidates_tables") != PHASE1_MVP_TABLES:
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

    patterns = data.get("forbidden_sql_patterns")
    if patterns != FORBIDDEN_SQL_PATTERNS:
        fail(f"forbidden_sql_patterns mismatch: {patterns!r}")


def validate_references(data: dict[str, Any]) -> None:
    refs = data.get("references")
    if not isinstance(refs, dict):
        fail("references missing or not object")

    expected = {
        "explicit_execution_gate_preview_json": "docs/phase1_mvp_db_schema_explicit_execution_gate_preview.json",
        "explicit_execution_gate_preview_step": "STEP157-B",
        "explicit_execution_gate_checker": "STEP157-C",
        "runtime_guard_preview_json": "docs/phase1_mvp_db_schema_runtime_guard_preview.json",
        "runtime_guard_preview_step": "STEP156-B",
        "execution_preview_json": "docs/phase1_mvp_db_schema_migration_execution_preview.json",
        "execution_preview_step": "STEP155-B",
        "migration_draft_script": "scripts/migrate_phase1_mvp_db_schema.py",
        "migration_draft_step": "STEP154-B",
    }

    for key, expected_value in expected.items():
        actual = refs.get(key)
        if actual != expected_value:
            fail(f"references.{key} expected {expected_value!r}, got {actual!r}")


def validate_key_policy(data: dict[str, Any]) -> None:
    key_policy = data.get("key_policy")
    if not isinstance(key_policy, dict):
        fail("key_policy missing or not object")

    expected = {
        "race_id_policy": "race_id = canonical_race_key",
        "canonical_race_key_policy": 'canonical_race_key = race_date + "_" + venue_id + "_" + race_no',
        "canonical_candidate_key_policy": 'canonical_candidate_key = race_id + "_" + lane',
    }

    for key, expected_value in expected.items():
        actual = key_policy.get(key)
        if actual != expected_value:
            fail(f"key_policy.{key} expected {expected_value!r}, got {actual!r}")


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

    for key, expected_value in expected.items():
        actual = safety.get(key)
        if actual != expected_value:
            fail(f"safety_decision.{key} expected {expected_value!r}, got {actual!r}")


def validate_protected_hashes(data: dict[str, Any]) -> None:
    hashes = data.get("protected_file_hashes")
    if not isinstance(hashes, dict):
        fail("protected_file_hashes missing or not object")

    required = [
        "db/schema.sql",
        "db/boatrace.sqlite3",
        "docs/prediction.json",
        "data/history_feature_config.json",
        "docs/phase1_mvp_db_schema_explicit_execution_gate_preview.json",
        "docs/phase1_mvp_db_schema_runtime_guard_preview.json",
        "docs/phase1_mvp_db_schema_migration_execution_preview.json",
    ]

    for key in required:
        value = hashes.get(key)
        if not isinstance(value, str) or len(value) != 64:
            fail(f"protected_file_hashes.{key} missing or invalid sha256")


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
    validate_compatibility_decisions(data)
    validate_pre_night_constraints(data)
    validate_pdf_operation_constraints(data)
    validate_ddl_audit(data)
    validate_references(data)
    validate_key_policy(data)
    validate_safety_decision(data)
    validate_protected_hashes(data)

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
        fail("final design compatibility preview JSON has uncommitted diff")
    if modified[str(EXPORTER_SCRIPT)]:
        fail("final design compatibility preview exporter has uncommitted diff")

    print("Phase 1 MVP DB schema final design compatibility preview validation: OK")
    print("STEP 158-C CHECK: OK")
    print(f"preview_type={data['preview_type']}")
    print(f"connection_mode={data['connection_mode']}")
    print(f"final_design_compatibility_preview_only={data['final_design_compatibility_preview_only']}")
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
    print(f"final_design_table_count={data['final_design_table_count']}")
    print(f"deferred_table_count={data['deferred_table_count']}")
    print(f"phase1_is_safe_subset_of_final_design={data['phase1_is_safe_subset_of_final_design']}")
    print(f"pre_night_only={data['pre_night_only']}")
    print(f"same_day_odds_allowed={data['same_day_odds_allowed']}")
    print(f"final_odds_allowed={data['final_odds_allowed']}")
    print(f"exhibition_data_allowed={data['exhibition_data_allowed']}")
    print(f"confirmed_outcomes_allowed={data['confirmed_outcomes_allowed']}")
    print(f"results_and_payouts_allowed_as_pre_night_inputs={data['results_and_payouts_allowed_as_pre_night_inputs']}")
    print(f"no_automatic_betting={data['no_automatic_betting']}")
    print(f"collection_interval_policy={data['collection_interval_policy']}")
    print(f"sqlite_commit_policy={data['sqlite_commit_policy']}")
    print(f"llm_usage_policy={data['llm_usage_policy']}")
    print(f"race_id_policy={data['key_policy']['race_id_policy']}")
    print(f"canonical_candidate_key_policy={data['key_policy']['canonical_candidate_key_policy']}")
    print(f"ddl_candidates_table_count={data['ddl_candidates_table_count']}")
    print(f"ddl_candidates_danger_pattern_count={data['ddl_candidates_danger_pattern_count']}")
    print(f"schema_sql_currently_modified={modified[str(SCHEMA_SQL)]}")
    print(f"database_currently_modified={modified[str(SQLITE_DB)]}")
    print(f"prediction_json_currently_modified={modified[str(PREDICTION_JSON)]}")
    print(f"config_currently_modified={modified[str(CONFIG_JSON)]}")
    print(f"final_design_compatibility_preview_currently_modified={modified[str(PREVIEW_JSON)]}")


if __name__ == "__main__":
    main()
