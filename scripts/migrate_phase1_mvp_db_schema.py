#!/usr/bin/env python3
"""
STEP154-B: Phase 1 MVP DB schema migration draft.

This script is a dry-run draft only.

It does not modify:
- db/schema.sql
- db/boatrace.sqlite3
- docs/prediction.json
- data/history_feature_config.json

It does not execute SQL.
It only prints candidate CREATE TABLE statements as preview text.
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
MIGRATION_PREVIEW_PATH = Path("docs/phase1_mvp_db_schema_migration_script_preview.json")
DDL_PREVIEW_PATH = Path("docs/phase1_mvp_db_schema_ddl_preview.json")

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

HISTORY_TABLES_TO_PRESERVE = [
    "history_races",
    "history_results",
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

DDL_CANDIDATES = {
    "races": """CREATE TABLE IF NOT EXISTS races (
  race_id TEXT PRIMARY KEY,
  canonical_race_key TEXT NOT NULL UNIQUE,
  race_date TEXT NOT NULL,
  venue_id TEXT NOT NULL,
  race_no INTEGER NOT NULL,
  venue_name TEXT,
  grade TEXT,
  race_type TEXT,
  distance INTEGER,
  title TEXT,
  is_night INTEGER,
  deadline_time TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);""",
    "entries": """CREATE TABLE IF NOT EXISTS entries (
  canonical_candidate_key TEXT PRIMARY KEY,
  race_id TEXT NOT NULL,
  canonical_race_key TEXT NOT NULL,
  race_date TEXT NOT NULL,
  venue_id TEXT NOT NULL,
  race_no INTEGER NOT NULL,
  lane INTEGER NOT NULL,
  racer_id TEXT,
  racer_name TEXT,
  class TEXT,
  branch TEXT,
  age INTEGER,
  weight REAL,
  motor_no TEXT,
  boat_no TEXT,
  entry_source_date TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);""",
    "feature_sets": """CREATE TABLE IF NOT EXISTS feature_sets (
  feature_set_id TEXT PRIMARY KEY,
  race_id TEXT NOT NULL,
  canonical_race_key TEXT NOT NULL,
  canonical_candidate_key TEXT,
  stage TEXT NOT NULL,
  as_of_time TEXT,
  feature_version TEXT NOT NULL,
  has_weather INTEGER NOT NULL DEFAULT 0,
  has_odds INTEGER NOT NULL DEFAULT 0,
  has_exhibition INTEGER NOT NULL DEFAULT 0,
  feature_hash TEXT,
  feature_file_path TEXT,
  feature_summary_json TEXT,
  created_at TEXT NOT NULL
);""",
    "prediction_runs": """CREATE TABLE IF NOT EXISTS prediction_runs (
  prediction_run_id TEXT PRIMARY KEY,
  race_id TEXT NOT NULL,
  canonical_race_key TEXT NOT NULL,
  stage TEXT NOT NULL,
  predicted_at TEXT NOT NULL,
  data_cutoff_at TEXT,
  model_version TEXT,
  feature_version TEXT,
  code_version TEXT,
  input_data_hash TEXT,
  feature_set_id TEXT,
  has_weather INTEGER NOT NULL DEFAULT 0,
  has_odds INTEGER NOT NULL DEFAULT 0,
  has_exhibition INTEGER NOT NULL DEFAULT 0,
  status TEXT,
  message TEXT,
  created_at TEXT NOT NULL
);""",
    "predictions": """CREATE TABLE IF NOT EXISTS predictions (
  prediction_id TEXT PRIMARY KEY,
  prediction_run_id TEXT NOT NULL,
  race_id TEXT NOT NULL,
  canonical_race_key TEXT NOT NULL,
  canonical_candidate_key TEXT,
  stage TEXT NOT NULL,
  bet_type TEXT,
  combination TEXT,
  predicted_probability REAL,
  odds REAL,
  expected_value REAL,
  recommended_stake INTEGER,
  rank INTEGER,
  is_recommended INTEGER,
  confidence TEXT,
  prediction_payload_json TEXT,
  created_at TEXT NOT NULL
);""",
    "results": """CREATE TABLE IF NOT EXISTS results (
  race_id TEXT NOT NULL,
  canonical_race_key TEXT NOT NULL,
  lane INTEGER NOT NULL,
  finish_position INTEGER,
  course INTEGER,
  start_timing REAL,
  decided_by TEXT,
  disqualified INTEGER,
  result_payload_json TEXT,
  created_at TEXT NOT NULL,
  PRIMARY KEY (race_id, lane)
);""",
    "payouts": """CREATE TABLE IF NOT EXISTS payouts (
  race_id TEXT NOT NULL,
  canonical_race_key TEXT NOT NULL,
  bet_type TEXT NOT NULL,
  combination TEXT NOT NULL,
  payout INTEGER,
  popularity INTEGER,
  payout_payload_json TEXT,
  created_at TEXT NOT NULL,
  PRIMARY KEY (race_id, bet_type, combination)
);""",
    "stage_metrics": """CREATE TABLE IF NOT EXISTS stage_metrics (
  stage_metric_id TEXT PRIMARY KEY,
  evaluated_at TEXT NOT NULL,
  period TEXT,
  stage TEXT NOT NULL,
  model_version TEXT,
  bet_type TEXT,
  races_count INTEGER,
  bets_count INTEGER,
  hit_count INTEGER,
  hit_rate REAL,
  total_stake INTEGER,
  total_payout INTEGER,
  profit INTEGER,
  roi REAL,
  logloss REAL,
  brier_score REAL,
  metric_payload_json TEXT,
  created_at TEXT NOT NULL
);""",
}


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
        fail(f"{path} must contain JSON object")
    return data


def git_diff_modified(path: Path) -> bool:
    result = subprocess.run(
        ["git", "diff", "--quiet", "--", str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode != 0


def assert_not_modified(path: Path, label: str) -> None:
    if git_diff_modified(path):
        fail(f"{label} has uncommitted diff")


def validate_config_disabled() -> None:
    config = load_json(CONFIG_PATH)
    if bool(config.get("enabled", False)):
        fail("data/history_feature_config.json enabled must remain false")


def validate_preview_inputs() -> None:
    preview = load_json(MIGRATION_PREVIEW_PATH)
    ddl_preview = load_json(DDL_PREVIEW_PATH)

    if preview.get("step") != "STEP153-B":
        fail("migration script preview step must be STEP153-B")
    if preview.get("preview_type") != "phase1-mvp-db-schema-migration-script-preview":
        fail("migration script preview_type mismatch")
    if preview.get("connection_mode") != "migration-preview-only":
        fail("migration script preview connection_mode mismatch")
    if preview.get("minimal_table_count") != 8:
        fail("migration script preview minimal_table_count must be 8")

    for key in [
        "creates_migration_script",
        "runs_migration",
        "executes_ddl",
        "writes_schema_sql",
        "writes_database",
        "creates_tables",
        "alters_tables",
        "drops_tables",
        "modifies_prediction_json",
        "writes_prediction_json",
        "prediction_core_connected",
        "config_enabled",
        "history_features_enabled",
    ]:
        if preview.get(key) is not False:
            fail(f"migration script preview {key} must be False")

    key_policy = preview.get("key_policy", {})
    if key_policy.get("race_id_policy") != "race_id = canonical_race_key":
        fail("race_id policy mismatch")
    if key_policy.get("canonical_candidate_key_policy") != "canonical_candidate_key = race_id + '_' + lane":
        fail("canonical candidate key policy mismatch")

    pdf = preview.get("pdf_operation_constraints", {})
    if pdf.get("no_automatic_betting") is not True:
        fail("no_automatic_betting must be True")
    if pdf.get("collection_interval_policy") != "5 to 15 minutes":
        fail("collection_interval_policy mismatch")
    if pdf.get("sqlite_commit_policy") != "nightly SQLite merge":
        fail("sqlite_commit_policy mismatch")
    if pdf.get("llm_usage_policy") != "LLM not used for normal prediction":
        fail("llm_usage_policy mismatch")

    if ddl_preview.get("step") != "STEP152-B":
        fail("DDL preview step must be STEP152-B")
    if ddl_preview.get("ddl_execution_mode") != "not-executed":
        fail("DDL preview execution mode must be not-executed")


def danger_tokens() -> list[str]:
    return [
        "DROP" + " TABLE",
        "DROP" + " INDEX",
        "ALTER" + " TABLE",
        "DELETE" + " FROM",
        "UPDATE" + " ",
        "INSERT" + " INTO",
        "REPLACE" + " INTO",
        "TRUNCATE",
    ]


def audit_candidate_sql() -> tuple[int, list[str]]:
    found: list[str] = []

    if list(DDL_CANDIDATES.keys()) != MINIMAL_TABLES:
        fail("DDL candidate table order mismatch")

    for table_name in MINIMAL_TABLES:
        ddl = DDL_CANDIDATES[table_name]
        ddl_upper = ddl.upper()

        if "CREATE TABLE IF NOT EXISTS" not in ddl_upper:
            fail(f"{table_name} candidate must contain CREATE TABLE IF NOT EXISTS")

        for token in danger_tokens():
            if token in ddl_upper:
                found.append(f"{table_name}:{token}")

    return len(found), found


def main() -> None:
    for path in [
        CONFIG_PATH,
        PREDICTION_PATH,
        SCHEMA_SQL_PATH,
        DB_PATH,
        MIGRATION_PREVIEW_PATH,
        DDL_PREVIEW_PATH,
    ]:
        if not path.exists():
            fail(f"missing required file: {path}")

    validate_config_disabled()
    validate_preview_inputs()

    for path, label in [
        (SCHEMA_SQL_PATH, "db/schema.sql"),
        (DB_PATH, "db/boatrace.sqlite3"),
        (PREDICTION_PATH, "docs/prediction.json"),
        (CONFIG_PATH, "data/history_feature_config.json"),
        (MIGRATION_PREVIEW_PATH, "docs/phase1_mvp_db_schema_migration_script_preview.json"),
        (DDL_PREVIEW_PATH, "docs/phase1_mvp_db_schema_ddl_preview.json"),
    ]:
        assert_not_modified(path, label)

    danger_count, danger_found = audit_candidate_sql()
    if danger_count != 0:
        fail("dangerous SQL token found in DDL candidates: " + ",".join(danger_found))

    print("Phase 1 MVP DB schema migration draft: OK")
    print("STEP 154-B CHECK: OK")
    print("mode=dry-run")
    print("executes_ddl=False")
    print("writes_database=False")
    print("writes_schema_sql=False")
    print("creates_tables=False")
    print("alters_tables=False")
    print("drops_tables=False")
    print("runs_migration=False")
    print("minimal_table_count=8")
    print("race_id_policy=race_id = canonical_race_key")
    print("canonical_candidate_key_policy=canonical_candidate_key = race_id + '_' + lane")
    print("history_tables_preserved=" + ",".join(HISTORY_TABLES_TO_PRESERVE))
    print("deferred_tables_not_included=" + ",".join(DEFERRED_TABLES))
    print(f"danger_pattern_count={danger_count}")
    print("danger_patterns=NONE")

    print()
    print("=== DDL candidate preview only; not executed ===")
    for table_name in MINIMAL_TABLES:
        print()
        print(f"-- table: {table_name}")
        print(DDL_CANDIDATES[table_name])


if __name__ == "__main__":
    main()
