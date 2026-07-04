#!/usr/bin/env python3
"""
STEP152-B: Export Phase 1 MVP DB schema DDL preview.

This exporter is design/preview only.

It writes only:
- docs/phase1_mvp_db_schema_ddl_preview.json

It must not modify:
- db/schema.sql
- db/boatrace.sqlite3
- docs/prediction.json
- data/history_feature_config.json

It must not execute DDL:
- no CREATE TABLE execution
- no ALTER TABLE execution
- no DROP TABLE execution
- no migration execution
"""

from __future__ import annotations

import json
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
OUTPUT_PATH = Path("docs/phase1_mvp_db_schema_ddl_preview.json")

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

PRE_NIGHT_FORBIDDEN_INFORMATION = [
    "same-day odds",
    "final odds",
    "exhibition data",
    "exhibition_time",
    "same-day weather",
    "same-day water condition",
    "results",
    "payouts",
    "confirmed race outcome",
    "post-race information",
]

DDL_PREVIEW_TABLES = [
    {
        "table_name": "races",
        "role": "Race-level master table for Phase 1 MVP.",
        "primary_key": ["canonical_race_key"],
        "key_policy": {
            "canonical_race_key_components": ["race_date", "venue_id", "race_no"],
        },
        "candidate_columns": [
            "canonical_race_key TEXT PRIMARY KEY",
            "race_date TEXT NOT NULL",
            "venue_id TEXT NOT NULL",
            "race_no INTEGER NOT NULL",
            "race_grade TEXT",
            "scheduled_deadline_at TEXT",
            "created_at TEXT NOT NULL",
            "updated_at TEXT NOT NULL",
        ],
        "candidate_ddl_preview": """CREATE TABLE IF NOT EXISTS races (
  canonical_race_key TEXT PRIMARY KEY,
  race_date TEXT NOT NULL,
  venue_id TEXT NOT NULL,
  race_no INTEGER NOT NULL,
  race_grade TEXT,
  scheduled_deadline_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);""",
    },
    {
        "table_name": "entries",
        "role": "Lane/candidate-level entry table for each race.",
        "primary_key": ["canonical_candidate_key"],
        "foreign_keys_preview": [
            {
                "column": "canonical_race_key",
                "references": "races(canonical_race_key)",
            }
        ],
        "key_policy": {
            "canonical_candidate_key_components": ["race_date", "venue_id", "race_no", "lane"],
        },
        "candidate_columns": [
            "canonical_candidate_key TEXT PRIMARY KEY",
            "canonical_race_key TEXT NOT NULL",
            "race_date TEXT NOT NULL",
            "venue_id TEXT NOT NULL",
            "race_no INTEGER NOT NULL",
            "lane INTEGER NOT NULL",
            "racer_id TEXT",
            "racer_name TEXT",
            "created_at TEXT NOT NULL",
            "updated_at TEXT NOT NULL",
        ],
        "candidate_ddl_preview": """CREATE TABLE IF NOT EXISTS entries (
  canonical_candidate_key TEXT PRIMARY KEY,
  canonical_race_key TEXT NOT NULL,
  race_date TEXT NOT NULL,
  venue_id TEXT NOT NULL,
  race_no INTEGER NOT NULL,
  lane INTEGER NOT NULL,
  racer_id TEXT,
  racer_name TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);""",
    },
    {
        "table_name": "feature_sets",
        "role": "PRE_NIGHT-safe feature snapshot metadata for each candidate.",
        "primary_key": ["feature_set_id"],
        "foreign_keys_preview": [
            {
                "column": "canonical_candidate_key",
                "references": "entries(canonical_candidate_key)",
            }
        ],
        "candidate_columns": [
            "feature_set_id TEXT PRIMARY KEY",
            "canonical_candidate_key TEXT NOT NULL",
            "canonical_race_key TEXT NOT NULL",
            "feature_version TEXT NOT NULL",
            "feature_stage TEXT NOT NULL",
            "feature_payload_json TEXT NOT NULL",
            "created_at TEXT NOT NULL",
        ],
        "candidate_ddl_preview": """CREATE TABLE IF NOT EXISTS feature_sets (
  feature_set_id TEXT PRIMARY KEY,
  canonical_candidate_key TEXT NOT NULL,
  canonical_race_key TEXT NOT NULL,
  feature_version TEXT NOT NULL,
  feature_stage TEXT NOT NULL,
  feature_payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);""",
    },
    {
        "table_name": "prediction_runs",
        "role": "Prediction run metadata table.",
        "primary_key": ["prediction_run_id"],
        "candidate_columns": [
            "prediction_run_id TEXT PRIMARY KEY",
            "run_stage TEXT NOT NULL",
            "model_version TEXT",
            "feature_version TEXT",
            "connection_mode TEXT NOT NULL",
            "created_at TEXT NOT NULL",
        ],
        "candidate_ddl_preview": """CREATE TABLE IF NOT EXISTS prediction_runs (
  prediction_run_id TEXT PRIMARY KEY,
  run_stage TEXT NOT NULL,
  model_version TEXT,
  feature_version TEXT,
  connection_mode TEXT NOT NULL,
  created_at TEXT NOT NULL
);""",
    },
    {
        "table_name": "predictions",
        "role": "Candidate-level prediction output archive table.",
        "primary_key": ["prediction_id"],
        "foreign_keys_preview": [
            {
                "column": "prediction_run_id",
                "references": "prediction_runs(prediction_run_id)",
            },
            {
                "column": "canonical_candidate_key",
                "references": "entries(canonical_candidate_key)",
            },
        ],
        "candidate_columns": [
            "prediction_id TEXT PRIMARY KEY",
            "prediction_run_id TEXT NOT NULL",
            "canonical_candidate_key TEXT NOT NULL",
            "canonical_race_key TEXT NOT NULL",
            "predicted_score REAL",
            "predicted_rank INTEGER",
            "prediction_payload_json TEXT NOT NULL",
            "created_at TEXT NOT NULL",
        ],
        "candidate_ddl_preview": """CREATE TABLE IF NOT EXISTS predictions (
  prediction_id TEXT PRIMARY KEY,
  prediction_run_id TEXT NOT NULL,
  canonical_candidate_key TEXT NOT NULL,
  canonical_race_key TEXT NOT NULL,
  predicted_score REAL,
  predicted_rank INTEGER,
  prediction_payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);""",
    },
    {
        "table_name": "results",
        "role": "Post-race result table. Not usable as PRE_NIGHT input.",
        "primary_key": ["canonical_race_key"],
        "candidate_columns": [
            "canonical_race_key TEXT PRIMARY KEY",
            "race_date TEXT NOT NULL",
            "venue_id TEXT NOT NULL",
            "race_no INTEGER NOT NULL",
            "result_payload_json TEXT NOT NULL",
            "created_at TEXT NOT NULL",
        ],
        "pre_night_input_allowed": False,
        "candidate_ddl_preview": """CREATE TABLE IF NOT EXISTS results (
  canonical_race_key TEXT PRIMARY KEY,
  race_date TEXT NOT NULL,
  venue_id TEXT NOT NULL,
  race_no INTEGER NOT NULL,
  result_payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);""",
    },
    {
        "table_name": "payouts",
        "role": "Post-race payout table. Not usable as PRE_NIGHT input.",
        "primary_key": ["canonical_race_key"],
        "candidate_columns": [
            "canonical_race_key TEXT PRIMARY KEY",
            "race_date TEXT NOT NULL",
            "venue_id TEXT NOT NULL",
            "race_no INTEGER NOT NULL",
            "payout_payload_json TEXT NOT NULL",
            "created_at TEXT NOT NULL",
        ],
        "pre_night_input_allowed": False,
        "candidate_ddl_preview": """CREATE TABLE IF NOT EXISTS payouts (
  canonical_race_key TEXT PRIMARY KEY,
  race_date TEXT NOT NULL,
  venue_id TEXT NOT NULL,
  race_no INTEGER NOT NULL,
  payout_payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);""",
    },
    {
        "table_name": "stage_metrics",
        "role": "Stage-level metrics and monitoring table.",
        "primary_key": ["stage_metric_id"],
        "candidate_columns": [
            "stage_metric_id TEXT PRIMARY KEY",
            "stage_name TEXT NOT NULL",
            "metric_name TEXT NOT NULL",
            "metric_value REAL",
            "metric_payload_json TEXT NOT NULL",
            "created_at TEXT NOT NULL",
        ],
        "candidate_ddl_preview": """CREATE TABLE IF NOT EXISTS stage_metrics (
  stage_metric_id TEXT PRIMARY KEY,
  stage_name TEXT NOT NULL,
  metric_name TEXT NOT NULL,
  metric_value REAL,
  metric_payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);""",
    },
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


def inspect_sqlite_db(path: Path) -> dict[str, Any]:
    exists = path.exists()
    info: dict[str, Any] = {
        "path": str(path),
        "exists": exists,
        "currently_modified": git_diff_modified(path) if exists else None,
        "table_names": [],
        "minimal_table_presence": {table: False for table in MINIMAL_TABLES},
        "history_table_presence": {table: False for table in HISTORY_TABLES},
    }

    if not exists:
        return info

    con = sqlite3.connect(path)
    try:
        rows = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        tables = [row[0] for row in rows]
        info["table_names"] = tables
        info["table_count"] = len(tables)
        info["minimal_table_presence"] = {
            table: table in tables for table in MINIMAL_TABLES
        }
        info["history_table_presence"] = {
            table: table in tables for table in HISTORY_TABLES
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


def validate_previous_previews() -> dict[str, Any]:
    schema_preview = load_json(PHASE1_SCHEMA_PREVIEW_PATH)
    implementation_plan_preview = load_json(IMPLEMENTATION_PLAN_PREVIEW_PATH)

    if schema_preview.get("step") != "STEP150-B":
        fail("docs/phase1_mvp_db_schema_preview.json step must be STEP150-B")
    if schema_preview.get("preview_type") != "phase1-mvp-db-schema":
        fail("docs/phase1_mvp_db_schema_preview.json preview_type mismatch")
    if schema_preview.get("minimal_table_count") != 8:
        fail("docs/phase1_mvp_db_schema_preview.json minimal_table_count must be 8")

    if implementation_plan_preview.get("step") != "STEP151-B":
        fail("implementation plan preview step must be STEP151-B")
    if (
        implementation_plan_preview.get("preview_type")
        != "phase1-mvp-db-schema-implementation-plan"
    ):
        fail("implementation plan preview_type mismatch")
    if implementation_plan_preview.get("connection_mode") != "planning-only":
        fail("implementation plan connection_mode must be planning-only")
    if implementation_plan_preview.get("minimal_table_count") != 8:
        fail("implementation plan minimal_table_count must be 8")

    for key in [
        "writes_schema_sql",
        "writes_database",
        "creates_tables",
        "alters_tables",
        "runs_migration",
        "modifies_prediction_json",
        "writes_prediction_json",
        "prediction_core_connected",
        "config_enabled",
        "history_features_enabled",
    ]:
        if implementation_plan_preview.get(key) is not False:
            fail(f"implementation plan {key} must be False")

    return {
        "schema_preview_step": schema_preview.get("step"),
        "schema_preview_type": schema_preview.get("preview_type"),
        "implementation_plan_step": implementation_plan_preview.get("step"),
        "implementation_plan_preview_type": implementation_plan_preview.get("preview_type"),
        "implementation_plan_connection_mode": implementation_plan_preview.get("connection_mode"),
    }


def main() -> None:
    config = load_json(CONFIG_PATH)

    config_enabled = bool(config.get("enabled", False))
    if config_enabled:
        fail("data/history_feature_config.json enabled must remain false")

    if not PREDICTION_PATH.exists():
        fail(f"missing required file: {PREDICTION_PATH}")
    if not SCHEMA_SQL_PATH.exists():
        fail(f"missing required file: {SCHEMA_SQL_PATH}")
    if not DB_PATH.exists():
        fail(f"missing required file: {DB_PATH}")

    previous_preview_validation = validate_previous_previews()
    schema_sql_inspection = inspect_schema_sql(SCHEMA_SQL_PATH)
    sqlite_db_inspection = inspect_sqlite_db(DB_PATH)

    minimal_table_presence_in_db = sqlite_db_inspection["minimal_table_presence"]
    missing_minimal_tables_in_db = [
        table for table, exists in minimal_table_presence_in_db.items() if not exists
    ]

    history_table_presence = sqlite_db_inspection["history_table_presence"]
    existing_history_tables_preserved = all(
        history_table_presence.get(table) is True for table in HISTORY_TABLES
    )

    preview: dict[str, Any] = {
        "step": "STEP152-B",
        "preview_type": "phase1-mvp-db-schema-ddl-preview",
        "connection_mode": "ddl-preview-only",
        "safe_mode": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_files": {
            "config": str(CONFIG_PATH),
            "prediction_json": str(PREDICTION_PATH),
            "schema_sql": str(SCHEMA_SQL_PATH),
            "sqlite_database": str(DB_PATH),
            "phase1_schema_preview": str(PHASE1_SCHEMA_PREVIEW_PATH),
            "implementation_plan_preview": str(IMPLEMENTATION_PLAN_PREVIEW_PATH),
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
        "ddl_execution_mode": "not-executed",
        "ddl_preview_only": True,
        "minimal_table_count": len(MINIMAL_TABLES),
        "minimal_tables": MINIMAL_TABLES,
        "implementation_order": IMPLEMENTATION_ORDER,
        "ddl_direction": {
            "add_only": True,
            "future_candidate_statement": "CREATE TABLE IF NOT EXISTS",
            "drop_table_allowed": False,
            "destructive_alter_allowed": False,
            "migration_execution_allowed_in_this_step": False,
            "schema_sql_write_allowed_in_this_step": False,
            "sqlite_write_allowed_in_this_step": False,
        },
        "canonical_keys": {
            "canonical_race_key": {
                "format": "race_date + '_' + venue_id + '_' + race_no",
                "components": ["race_date", "venue_id", "race_no"],
            },
            "canonical_candidate_key": {
                "format": "race_date + '_' + venue_id + '_' + race_no + '_' + lane",
                "components": ["race_date", "venue_id", "race_no", "lane"],
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
        "ddl_preview_tables": DDL_PREVIEW_TABLES,
        "existing_history_tables_policy": {
            "policy": "preserve",
            "existing_history_tables_preserved": existing_history_tables_preserved,
            "tables": HISTORY_TABLES,
            "drop_allowed": False,
            "recreate_allowed": False,
            "destructive_alter_allowed": False,
        },
        "pre_night_safety_constraints": {
            "pre_night_only": True,
            "forbidden_information": PRE_NIGHT_FORBIDDEN_INFORMATION,
            "results_and_payouts_allowed_as_training_labels_after_race": True,
            "results_and_payouts_allowed_as_pre_night_inputs": False,
        },
        "current_repository_state": {
            "schema_sql": schema_sql_inspection,
            "sqlite_database": sqlite_db_inspection,
            "prediction_json_currently_modified": git_diff_modified(PREDICTION_PATH),
            "config_currently_modified": git_diff_modified(CONFIG_PATH),
            "missing_minimal_tables_in_database": missing_minimal_tables_in_db,
        },
        "previous_preview_validation": previous_preview_validation,
        "safety_decisions": {
            "do_not_modify_schema_sql_in_step152_b": True,
            "do_not_modify_sqlite_db_in_step152_b": True,
            "do_not_execute_create_table_in_step152_b": True,
            "do_not_execute_alter_table_in_step152_b": True,
            "do_not_execute_drop_table_in_step152_b": True,
            "do_not_run_migration_in_step152_b": True,
            "do_not_modify_prediction_json": True,
            "do_not_enable_history_features": True,
            "do_not_connect_prediction_core": True,
        },
        "next_step": {
            "step": "STEP152-C",
            "description": "Create checker for Phase 1 MVP DB schema DDL preview JSON.",
        },
    }

    if preview["minimal_table_count"] != 8:
        fail("minimal_table_count must be 8")
    if preview["implementation_order"] != MINIMAL_TABLES:
        fail("implementation_order must match minimal table order")
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
    ]:
        if preview.get(key) is not False:
            fail(f"{key} must be False")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(preview, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print("Phase 1 MVP DB schema DDL preview export: OK")
    print("STEP 152-B CHECK: OK")
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
    print(f"minimal_table_count={preview['minimal_table_count']}")


if __name__ == "__main__":
    main()
