#!/usr/bin/env python3
"""
STEP153-B: Export Phase 1 MVP DB schema migration script preview.

This exporter creates only a preview JSON.

It writes only:
- docs/phase1_mvp_db_schema_migration_script_preview.json

It must not create a migration script.
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
- no INSERT / UPDATE / DELETE execution
- no migration execution
"""

from __future__ import annotations

import json
import re
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CONFIG_PATH = Path("data/history_feature_config.json")
PREDICTION_PATH = Path("docs/prediction.json")
SCHEMA_SQL_PATH = Path("db/schema.sql")
DB_PATH = Path("db/boatrace.sqlite3")

PHASE1_SCHEMA_PREVIEW_PATH = Path("docs/phase1_mvp_db_schema_preview.json")
IMPLEMENTATION_PLAN_PREVIEW_PATH = Path("docs/phase1_mvp_db_schema_implementation_plan_preview.json")
DDL_PREVIEW_PATH = Path("docs/phase1_mvp_db_schema_ddl_preview.json")

OUTPUT_PATH = Path("docs/phase1_mvp_db_schema_migration_script_preview.json")

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

IMPLEMENTATION_ORDER = [
    "races",
    "entries",
    "feature_sets",
    "prediction_runs",
    "predictions",
    "results",
    "payouts",
    "stage_metrics",
]

HISTORY_TABLES = [
    "history_races",
    "history_results",
]

DEFERRED_FINAL_DESIGN_TABLES = [
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

PRE_NIGHT_FORBIDDEN_INFORMATION = [
    "same-day odds",
    "final odds",
    "exhibition data",
    "exhibition_time",
    "exhibition ST",
    "exhibition course",
    "same-day weather",
    "same-day water condition",
    "results",
    "payouts",
    "confirmed race outcome",
    "post-race information",
]

DANGER_PATTERNS = [
    r"\bDROP\s+TABLE\b",
    r"\bDROP\s+INDEX\b",
    r"\bALTER\s+TABLE\b",
    r"\bDELETE\s+FROM\b",
    r"\bTRUNCATE\b",
    r"\bREPLACE\s+INTO\b",
    r"\bUPDATE\b",
    r"\bINSERT\s+INTO\b",
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


def git_diff_modified(path: Path) -> bool:
    result = subprocess.run(
        ["git", "diff", "--quiet", "--", str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode != 0


def inspect_sqlite_db(path: Path) -> dict[str, Any]:
    info: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "currently_modified": git_diff_modified(path) if path.exists() else None,
        "table_names": [],
        "table_count": None,
        "history_table_presence": {table: False for table in HISTORY_TABLES},
        "minimal_table_presence": {table: False for table in MINIMAL_TABLES},
    }

    if not path.exists():
        return info

    con = sqlite3.connect(path)
    try:
        rows = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        tables = [row[0] for row in rows]
        info["table_names"] = tables
        info["table_count"] = len(tables)
        info["history_table_presence"] = {
            table: table in tables for table in HISTORY_TABLES
        }
        info["minimal_table_presence"] = {
            table: table in tables for table in MINIMAL_TABLES
        }

        row_counts: dict[str, int | None] = {}
        for table in HISTORY_TABLES:
            if table in tables:
                try:
                    row_counts[table] = int(
                        con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                    )
                except Exception:
                    row_counts[table] = None
        info["history_table_row_counts"] = row_counts
    finally:
        con.close()

    return info


def inspect_schema_sql(path: Path) -> dict[str, Any]:
    exists = path.exists()
    text = path.read_text(encoding="utf-8") if exists else ""
    lower_text = text.lower()

    return {
        "path": str(path),
        "exists": exists,
        "line_count": len(text.splitlines()) if exists else None,
        "currently_modified": git_diff_modified(path) if exists else None,
        "minimal_table_name_mentions": {
            table: table.lower() in lower_text for table in MINIMAL_TABLES
        },
        "history_table_name_mentions": {
            table: table.lower() in lower_text for table in HISTORY_TABLES
        },
    }


def validate_previous_previews() -> dict[str, Any]:
    schema_preview = load_json(PHASE1_SCHEMA_PREVIEW_PATH)
    implementation_preview = load_json(IMPLEMENTATION_PLAN_PREVIEW_PATH)
    ddl_preview = load_json(DDL_PREVIEW_PATH)

    if schema_preview.get("step") != "STEP150-B":
        fail("phase1 schema preview step must be STEP150-B")
    if schema_preview.get("preview_type") != "phase1-mvp-db-schema":
        fail("phase1 schema preview_type mismatch")
    if schema_preview.get("minimal_table_count") != 8:
        fail("phase1 schema preview minimal_table_count must be 8")

    if implementation_preview.get("step") != "STEP151-B":
        fail("implementation plan preview step must be STEP151-B")
    if implementation_preview.get("preview_type") != "phase1-mvp-db-schema-implementation-plan":
        fail("implementation plan preview_type mismatch")
    if implementation_preview.get("connection_mode") != "planning-only":
        fail("implementation plan connection_mode must be planning-only")
    if implementation_preview.get("minimal_table_count") != 8:
        fail("implementation plan minimal_table_count must be 8")

    if ddl_preview.get("step") != "STEP152-B":
        fail("DDL preview step must be STEP152-B")
    if ddl_preview.get("preview_type") != "phase1-mvp-db-schema-ddl-preview":
        fail("DDL preview_type mismatch")
    if ddl_preview.get("connection_mode") != "ddl-preview-only":
        fail("DDL preview connection_mode must be ddl-preview-only")
    if ddl_preview.get("ddl_execution_mode") != "not-executed":
        fail("DDL preview ddl_execution_mode must be not-executed")
    if ddl_preview.get("ddl_preview_only") is not True:
        fail("DDL preview ddl_preview_only must be True")
    if ddl_preview.get("minimal_table_count") != 8:
        fail("DDL preview minimal_table_count must be 8")

    for key in [
        "writes_schema_sql",
        "writes_database",
        "creates_tables",
        "alters_tables",
        "drops_tables",
        "runs_migration",
        "executes_ddl",
        "modifies_prediction_json",
        "writes_prediction_json",
        "prediction_core_connected",
        "config_enabled",
        "history_features_enabled",
    ]:
        if ddl_preview.get(key) is not False:
            fail(f"DDL preview {key} must be False")

    ddl_direction = ddl_preview.get("ddl_direction")
    if not isinstance(ddl_direction, dict):
        fail("DDL preview ddl_direction must be object")
    if ddl_direction.get("add_only") is not True:
        fail("DDL preview ddl_direction.add_only must be True")
    if ddl_direction.get("future_candidate_statement") != "CREATE TABLE IF NOT EXISTS":
        fail("DDL preview future_candidate_statement must be CREATE TABLE IF NOT EXISTS")
    if ddl_direction.get("drop_table_allowed") is not False:
        fail("DDL preview drop_table_allowed must be False")
    if ddl_direction.get("destructive_alter_allowed") is not False:
        fail("DDL preview destructive_alter_allowed must be False")

    return {
        "schema_preview": {
            "step": schema_preview.get("step"),
            "preview_type": schema_preview.get("preview_type"),
            "minimal_table_count": schema_preview.get("minimal_table_count"),
        },
        "implementation_plan_preview": {
            "step": implementation_preview.get("step"),
            "preview_type": implementation_preview.get("preview_type"),
            "connection_mode": implementation_preview.get("connection_mode"),
            "minimal_table_count": implementation_preview.get("minimal_table_count"),
        },
        "ddl_preview": {
            "step": ddl_preview.get("step"),
            "preview_type": ddl_preview.get("preview_type"),
            "connection_mode": ddl_preview.get("connection_mode"),
            "ddl_execution_mode": ddl_preview.get("ddl_execution_mode"),
            "ddl_preview_only": ddl_preview.get("ddl_preview_only"),
            "minimal_table_count": ddl_preview.get("minimal_table_count"),
        },
    }


def audit_ddl_preview_candidates(ddl_preview: dict[str, Any]) -> list[dict[str, Any]]:
    tables = ddl_preview.get("ddl_preview_tables")
    if not isinstance(tables, list):
        fail("DDL preview ddl_preview_tables must be list")

    audit: list[dict[str, Any]] = []
    for item in tables:
        if not isinstance(item, dict):
            fail("DDL preview table item must be object")
        table_name = item.get("table_name")
        ddl = item.get("candidate_ddl_preview", "")
        if not isinstance(table_name, str) or not table_name:
            fail("DDL preview table_name must be non-empty string")
        if not isinstance(ddl, str) or not ddl.strip():
            fail(f"DDL preview candidate_ddl_preview missing for {table_name}")

        found = [
            pattern for pattern in DANGER_PATTERNS
            if re.search(pattern, ddl, flags=re.IGNORECASE)
        ]

        audit.append(
            {
                "table_name": table_name,
                "has_create_table_if_not_exists": "CREATE TABLE IF NOT EXISTS" in ddl.upper(),
                "danger_pattern_count": len(found),
                "danger_patterns": found,
                "candidate_ddl_not_executed": True,
            }
        )

    return audit


def main() -> None:
    config = load_json(CONFIG_PATH)

    config_enabled = bool(config.get("enabled", False))
    if config_enabled:
        fail("data/history_feature_config.json enabled must remain false")

    for path in [
        PREDICTION_PATH,
        SCHEMA_SQL_PATH,
        DB_PATH,
        PHASE1_SCHEMA_PREVIEW_PATH,
        IMPLEMENTATION_PLAN_PREVIEW_PATH,
        DDL_PREVIEW_PATH,
    ]:
        if not path.exists():
            fail(f"missing required file: {path}")

    previous_preview_validation = validate_previous_previews()
    ddl_preview = load_json(DDL_PREVIEW_PATH)
    ddl_candidate_audit = audit_ddl_preview_candidates(ddl_preview)

    for item in ddl_candidate_audit:
        if item["has_create_table_if_not_exists"] is not True:
            fail(f"{item['table_name']} must contain CREATE TABLE IF NOT EXISTS")
        if item["danger_pattern_count"] != 0:
            fail(f"{item['table_name']} contains dangerous DDL/DML pattern: {item['danger_patterns']}")

    sqlite_inspection = inspect_sqlite_db(DB_PATH)
    schema_inspection = inspect_schema_sql(SCHEMA_SQL_PATH)

    history_table_presence = sqlite_inspection.get("history_table_presence", {})
    existing_history_tables_preserved = all(
        history_table_presence.get(table) is True for table in HISTORY_TABLES
    )

    preview: dict[str, Any] = {
        "step": "STEP153-B",
        "preview_type": "phase1-mvp-db-schema-migration-script-preview",
        "connection_mode": "migration-preview-only",
        "safe_mode": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_files": {
            "config": str(CONFIG_PATH),
            "prediction_json": str(PREDICTION_PATH),
            "schema_sql": str(SCHEMA_SQL_PATH),
            "sqlite_database": str(DB_PATH),
            "phase1_schema_preview": str(PHASE1_SCHEMA_PREVIEW_PATH),
            "implementation_plan_preview": str(IMPLEMENTATION_PLAN_PREVIEW_PATH),
            "ddl_preview": str(DDL_PREVIEW_PATH),
        },
        "output": str(OUTPUT_PATH),
        "config_enabled": False,
        "history_features_enabled": False,
        "prediction_core_connected": False,
        "modifies_prediction_json": False,
        "writes_prediction_json": False,
        "writes_schema_sql": False,
        "writes_database": False,
        "creates_tables": False,
        "alters_tables": False,
        "drops_tables": False,
        "runs_migration": False,
        "executes_ddl": False,
        "creates_migration_script": False,
        "migration_script_preview_only": True,
        "migration_script_execution_mode": "not-created-not-executed",
        "ddl_execution_mode": "not-executed",
        "minimal_table_count": len(MINIMAL_TABLES),
        "minimal_tables": MINIMAL_TABLES,
        "implementation_order": IMPLEMENTATION_ORDER,
        "migration_script_design_direction": {
            "add_only": True,
            "idempotent": True,
            "future_candidate_statement": "CREATE TABLE IF NOT EXISTS",
            "guarded_by_safety_checks": True,
            "requires_pre_migration_hash_record": True,
            "requires_sqlite_backup_before_execution": True,
            "drop_table_allowed": False,
            "drop_index_allowed": False,
            "destructive_alter_allowed": False,
            "delete_from_history_tables_allowed": False,
            "update_history_tables_allowed": False,
            "replace_into_history_tables_allowed": False,
            "migration_execution_allowed_in_this_step": False,
            "schema_sql_write_allowed_in_this_step": False,
            "sqlite_write_allowed_in_this_step": False,
            "migration_script_file_created_in_this_step": False,
        },
        "ddl_candidate_audit": ddl_candidate_audit,
        "key_policy": {
            "race_id_policy": "race_id = canonical_race_key",
            "canonical_race_key": {
                "format": "race_date + '_' + venue_id + '_' + race_no",
                "components": ["race_date", "venue_id", "race_no"],
            },
            "canonical_candidate_key_policy": "canonical_candidate_key = race_id + '_' + lane",
            "canonical_candidate_key": {
                "format": "race_date + '_' + venue_id + '_' + race_no + '_' + lane",
                "components": ["race_date", "venue_id", "race_no", "lane"],
            },
            "pdf_entries_primary_key_mapping": {
                "pdf_primary_key": ["race_id", "lane"],
                "phase1_equivalent": "canonical_candidate_key",
            },
            "not_primary_key_components": [
                "racer_name",
                "motor_no",
                "boat_no",
                "odds",
                "exhibition_time",
                "weather",
                "result",
                "payout",
            ],
        },
        "existing_history_tables_policy": {
            "policy": "preserve",
            "existing_history_tables_preserved": existing_history_tables_preserved,
            "tables": HISTORY_TABLES,
            "drop_allowed": False,
            "recreate_allowed": False,
            "destructive_alter_allowed": False,
            "delete_allowed": False,
            "update_allowed": False,
        },
        "final_design_pdf_compatibility": {
            "phase1_is_safe_subset_of_final_design": True,
            "covered_phase1_tables": MINIMAL_TABLES,
            "deferred_final_design_tables": DEFERRED_FINAL_DESIGN_TABLES,
            "deferred_tables_not_forgotten": True,
            "phase_mapping": {
                "Phase 1": [
                    "PRE_NIGHT prediction",
                    "PRE_NIGHT evaluation",
                    "minimal DB schema",
                ],
                "Phase 2": [
                    "MORNING update",
                    "weather_water_snapshots",
                ],
                "Phase 3": [
                    "POST_EXHIBITION update",
                    "exhibition_snapshots",
                ],
                "Phase 4": [
                    "odds_snapshots",
                    "expected value",
                    "FINAL stage",
                    "prediction_changes",
                ],
                "Phase 5": [
                    "stage_transition_metrics",
                    "model_registry",
                    "training_runs",
                    "LLM weekly evaluation analysis",
                ],
            },
        },
        "pdf_operation_constraints": {
            "no_automatic_betting": True,
            "collection_interval_policy": "5 to 15 minutes",
            "avoid_high_frequency_fetching": True,
            "cache_fetched_data": True,
            "fallback_on_failure": True,
            "intraday_updates": "JSON-centered updates",
            "sqlite_commit_policy": "nightly SQLite merge",
            "llm_usage_policy": "LLM not used for normal prediction",
            "llm_allowed_scope": "weekly evaluation analysis only",
            "smartphone_operation_supported": True,
        },
        "pre_night_safety_constraints": {
            "pre_night_only": True,
            "forbidden_information": PRE_NIGHT_FORBIDDEN_INFORMATION,
            "results_and_payouts_allowed_as_training_labels_after_race": True,
            "results_and_payouts_allowed_as_pre_night_inputs": False,
        },
        "rollback_requirements_for_future_migration": {
            "record_git_status": True,
            "record_git_hash": True,
            "record_schema_sql_sha256": True,
            "record_sqlite_db_sha256": True,
            "record_prediction_json_sha256": True,
            "record_config_sha256": True,
            "record_existing_sqlite_table_list": True,
            "record_history_races_row_count": True,
            "record_history_results_row_count": True,
            "create_sqlite_backup_before_execution": True,
            "restore_path_required": True,
        },
        "current_repository_state": {
            "schema_sql": schema_inspection,
            "sqlite_database": sqlite_inspection,
            "prediction_json_currently_modified": git_diff_modified(PREDICTION_PATH),
            "config_currently_modified": git_diff_modified(CONFIG_PATH),
            "ddl_preview_currently_modified": git_diff_modified(DDL_PREVIEW_PATH),
        },
        "previous_preview_validation": previous_preview_validation,
        "safety_decisions": {
            "do_not_create_migration_script_in_step153_b": True,
            "do_not_execute_migration_in_step153_b": True,
            "do_not_execute_ddl_in_step153_b": True,
            "do_not_modify_schema_sql_in_step153_b": True,
            "do_not_modify_sqlite_db_in_step153_b": True,
            "do_not_modify_prediction_json": True,
            "do_not_modify_ddl_preview_json": True,
            "do_not_enable_history_features": True,
            "do_not_connect_prediction_core": True,
            "do_not_change_prediction_scores_or_ranks": True,
            "do_not_add_dashboard_ui": True,
        },
        "next_step": {
            "step": "STEP153-C",
            "description": "Create checker for Phase 1 MVP DB schema migration script preview JSON.",
        },
    }

    for key in [
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
    ]:
        if preview.get(key) is not False:
            fail(f"{key} must be False")

    if preview["minimal_table_count"] != 8:
        fail("minimal_table_count must be 8")
    if preview["minimal_tables"] != MINIMAL_TABLES:
        fail("minimal_tables mismatch")
    if preview["implementation_order"] != IMPLEMENTATION_ORDER:
        fail("implementation_order mismatch")
    if preview["migration_script_preview_only"] is not True:
        fail("migration_script_preview_only must be True")

    for protected_path, label in [
        (SCHEMA_SQL_PATH, "db/schema.sql"),
        (DB_PATH, "db/boatrace.sqlite3"),
        (PREDICTION_PATH, "docs/prediction.json"),
        (CONFIG_PATH, "data/history_feature_config.json"),
        (DDL_PREVIEW_PATH, "docs/phase1_mvp_db_schema_ddl_preview.json"),
    ]:
        if git_diff_modified(protected_path):
            fail(f"{label} has uncommitted diff")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(preview, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print("Phase 1 MVP DB schema migration script preview export: OK")
    print("STEP 153-B CHECK: OK")
    print(f"preview_type={preview['preview_type']}")
    print(f"connection_mode={preview['connection_mode']}")
    print(f"config_enabled={preview['config_enabled']}")
    print(f"history_features_enabled={preview['history_features_enabled']}")
    print(f"prediction_core_connected={preview['prediction_core_connected']}")
    print(f"modifies_prediction_json={preview['modifies_prediction_json']}")
    print(f"writes_prediction_json={preview['writes_prediction_json']}")
    print(f"writes_schema_sql={preview['writes_schema_sql']}")
    print(f"writes_database={preview['writes_database']}")
    print(f"creates_tables={preview['creates_tables']}")
    print(f"alters_tables={preview['alters_tables']}")
    print(f"drops_tables={preview['drops_tables']}")
    print(f"runs_migration={preview['runs_migration']}")
    print(f"executes_ddl={preview['executes_ddl']}")
    print(f"creates_migration_script={preview['creates_migration_script']}")
    print(f"minimal_table_count={preview['minimal_table_count']}")


if __name__ == "__main__":
    main()
