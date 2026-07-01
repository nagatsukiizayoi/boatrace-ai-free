from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CONFIG_PATH = Path("data/history_feature_config.json")
PREDICTION_PATH = Path("docs/prediction.json")
SCHEMA_SQL_PATH = Path("db/schema.sql")
DB_PATH = Path("db/boatrace.sqlite3")
SCHEMA_PREVIEW_PATH = Path("docs/phase1_mvp_db_schema_preview.json")
OUTPUT_PATH = Path("docs/phase1_mvp_db_schema_implementation_plan_preview.json")


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


def git_has_diff(path: Path) -> bool:
    result = subprocess.run(
        ["git", "diff", "--quiet", "--", str(path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode == 0:
        return False

    if result.returncode == 1:
        return True

    fail(f"git diff check failed for {path}: {result.stderr.strip()}")
    return True


def inspect_database() -> dict[str, Any]:
    info: dict[str, Any] = {
        "db_path": str(DB_PATH),
        "db_exists": DB_PATH.exists(),
        "tables": [],
        "table_count": None,
        "history_results_exists": False,
        "history_races_exists": False,
        "history_results_row_count": None,
        "history_races_row_count": None,
        "phase1_table_presence": {},
    }

    if not DB_PATH.exists():
        return info

    con = sqlite3.connect(DB_PATH)
    try:
        tables = [
            row[0]
            for row in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
        ]

        info["tables"] = tables
        info["table_count"] = len(tables)

        for table in ["history_results", "history_races"]:
            exists = table in tables
            info[f"{table}_exists"] = exists
            if exists:
                count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                info[f"{table}_row_count"] = count

        info["phase1_table_presence"] = {
            table: table in tables
            for table in MINIMAL_TABLES
        }
    finally:
        con.close()

    return info


def inspect_schema_sql() -> dict[str, Any]:
    info: dict[str, Any] = {
        "schema_sql_path": str(SCHEMA_SQL_PATH),
        "schema_sql_exists": SCHEMA_SQL_PATH.exists(),
        "line_count": None,
        "contains_phase1_table_names": {},
    }

    if not SCHEMA_SQL_PATH.exists():
        return info

    text = SCHEMA_SQL_PATH.read_text(encoding="utf-8")
    info["line_count"] = len(text.splitlines())
    info["contains_phase1_table_names"] = {
        table: table in text
        for table in MINIMAL_TABLES
    }

    return info


def main() -> None:
    config = load_json(CONFIG_PATH)
    schema_preview = load_json(SCHEMA_PREVIEW_PATH)

    if not isinstance(config, dict):
        fail(f"{CONFIG_PATH} must contain JSON object")

    if config.get("enabled") is not False:
        fail(f"history feature config must remain enabled:false, got {config.get('enabled')!r}")

    if not isinstance(schema_preview, dict):
        fail(f"{SCHEMA_PREVIEW_PATH} must contain JSON object")

    if schema_preview.get("step") != "STEP150-B":
        fail(f"schema preview step must be STEP150-B, got {schema_preview.get('step')!r}")

    if schema_preview.get("preview_type") != "phase1-mvp-db-schema":
        fail(f"schema preview type mismatch: {schema_preview.get('preview_type')!r}")

    if schema_preview.get("connection_mode") != "design-only":
        fail(f"schema preview connection_mode must be design-only, got {schema_preview.get('connection_mode')!r}")

    for key in [
        "writes_schema_sql",
        "writes_database",
        "creates_tables",
        "alters_tables",
        "modifies_prediction_json",
        "prediction_core_connected",
        "config_enabled",
        "history_features_enabled",
    ]:
        if schema_preview.get(key) is not False:
            fail(f"schema preview {key} must be False, got {schema_preview.get(key)!r}")

    minimal_names = schema_preview.get("minimal_table_names")
    if minimal_names != MINIMAL_TABLES:
        fail(f"minimal_table_names mismatch: {minimal_names!r}")

    if not PREDICTION_PATH.exists():
        fail(f"missing file: {PREDICTION_PATH}")

    schema_sql_currently_modified = git_has_diff(SCHEMA_SQL_PATH) if SCHEMA_SQL_PATH.exists() else False
    database_currently_modified = git_has_diff(DB_PATH) if DB_PATH.exists() else False
    prediction_json_currently_modified = git_has_diff(PREDICTION_PATH)

    result = {
        "step": "STEP151-B",
        "preview_type": "phase1-mvp-db-schema-implementation-plan",
        "connection_mode": "planning-only",
        "safe_mode": True,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "config_enabled": False,
        "history_features_enabled": False,
        "prediction_core_connected": False,
        "affects_prediction_output": False,
        "modifies_prediction_json": False,
        "writes_prediction_json": False,
        "writes_schema_sql": False,
        "writes_database": False,
        "creates_tables": False,
        "alters_tables": False,
        "runs_migration": False,
        "source_files": {
            "history_feature_config": str(CONFIG_PATH),
            "prediction_json": str(PREDICTION_PATH),
            "schema_sql": str(SCHEMA_SQL_PATH),
            "database": str(DB_PATH),
            "phase1_mvp_db_schema_preview": str(SCHEMA_PREVIEW_PATH),
        },
        "output_file": str(OUTPUT_PATH),
        "schema_sql_currently_modified": schema_sql_currently_modified,
        "database_currently_modified": database_currently_modified,
        "prediction_json_currently_modified": prediction_json_currently_modified,
        "schema_sql_inspection": inspect_schema_sql(),
        "database_inspection": inspect_database(),
        "minimal_tables": MINIMAL_TABLES,
        "minimal_table_count": len(MINIMAL_TABLES),
        "implementation_order": IMPLEMENTATION_ORDER,
        "implementation_order_reason": [
            "races must exist before entries, prediction_runs, predictions, results, and payouts",
            "entries depends on race_id and lane",
            "feature_sets and prediction_runs depend on race_id",
            "predictions depends on prediction_runs and race_id",
            "results and payouts depend on race_id",
            "stage_metrics aggregates evaluation results",
        ],
        "canonical_keys": {
            "canonical_race_key": {
                "components": ["race_date", "venue_id", "race_no"],
                "recommended_format": "race_date + '_' + venue_id + '_' + race_no",
            },
            "canonical_candidate_key": {
                "components": ["race_date", "venue_id", "race_no", "lane"],
                "recommended_format": "race_date + '_' + venue_id + '_' + race_no + '_' + lane",
            },
        },
        "existing_history_tables_policy": {
            "preserve_history_results": True,
            "preserve_history_races": True,
            "do_not_remove_existing_history_tables": True,
            "reason": "existing history tables are required for readiness and history feature checks",
        },
        "schema_implementation_policy": {
            "preview_before_schema_sql_change": True,
            "checker_before_database_change": True,
            "rollback_policy_required_before_migration": True,
            "schema_sql_changes_should_be_isolated": True,
            "database_changes_should_be_isolated": True,
            "no_prediction_output_change_during_schema_implementation": True,
        },
        "rollback_policy": {
            "record_schema_sql_hash_before_change": True,
            "record_database_hash_before_change": True,
            "restore_schema_sql_command": "git restore db/schema.sql",
            "restore_prediction_json_command": "git restore docs/prediction.json",
            "do_not_blindly_delete_database": True,
            "if_history_tables_missing_rebuild_only_when_instructed": True,
        },
        "pre_night_safety_constraints": [
            "PRE_NIGHT must not use same-day odds",
            "PRE_NIGHT must not use exhibition_time",
            "PRE_NIGHT must not use exhibition_st",
            "PRE_NIGHT must not use exhibition_course",
            "PRE_NIGHT must not use same-day wind_speed",
            "PRE_NIGHT must not use same-day wave_height",
            "PRE_NIGHT must not use same-day weather or water information unavailable at previous night",
            "PRE_NIGHT must not use results as features",
            "PRE_NIGHT must not use payouts as features",
        ],
        "future_schema_implementation_steps": [
            {
                "step": "future STEP152-A or later",
                "action": "prepare schema.sql change preview",
                "writes_schema_sql": False,
                "writes_database": False,
            },
            {
                "step": "future schema implementation step",
                "action": "modify db/schema.sql only after preview and checker",
                "writes_schema_sql": True,
                "writes_database": False,
            },
            {
                "step": "future migration preview step",
                "action": "prepare database migration preview",
                "writes_schema_sql": False,
                "writes_database": False,
            },
            {
                "step": "future controlled migration step",
                "action": "create Phase 1 MVP tables only after rollback checks",
                "writes_schema_sql": False,
                "writes_database": True,
            },
        ],
        "safety_decision": {
            "do_not_enable_history_features": True,
            "do_not_connect_prediction_core": True,
            "do_not_modify_prediction_json": True,
            "do_not_modify_schema_sql_in_step151b": True,
            "do_not_modify_database_in_step151b": True,
            "do_not_create_tables_in_step151b": True,
            "do_not_run_migration_in_step151b": True,
            "do_not_change_prediction_scores": True,
            "do_not_change_ranks": True,
            "do_not_change_recommendations": True,
            "do_not_change_expected_values": True,
        },
        "next_step": {
            "step": "STEP151-C",
            "purpose": "add a checker for this schema implementation plan preview",
        },
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("Phase 1 MVP DB schema implementation plan preview export: OK")
    print("STEP 151-B CHECK: OK")
    print(f"output={OUTPUT_PATH}")
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
    print(f"minimal_table_count={len(MINIMAL_TABLES)}")
    print("implementation_order=" + ",".join(IMPLEMENTATION_ORDER))
    print(f"schema_sql_currently_modified={schema_sql_currently_modified}")
    print(f"database_currently_modified={database_currently_modified}")
    print(f"prediction_json_currently_modified={prediction_json_currently_modified}")


if __name__ == "__main__":
    main()
