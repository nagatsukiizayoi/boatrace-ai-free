from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CONFIG_PATH = Path("data/history_feature_config.json")
PREDICTION_PATH = Path("docs/prediction.json")
SCHEMA_SQL_PATH = Path("db/schema.sql")
DB_PATH = Path("db/boatrace.sqlite3")
OUTPUT_PATH = Path("docs/phase1_mvp_db_schema_preview.json")


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


def inspect_existing_database() -> dict[str, Any]:
    info: dict[str, Any] = {
        "db_path": str(DB_PATH),
        "db_exists": DB_PATH.exists(),
        "table_count": None,
        "tables": [],
        "history_results_exists": False,
        "history_races_exists": False,
        "history_results_row_count": None,
        "history_races_row_count": None,
    }

    if not DB_PATH.exists():
        return info

    con = sqlite3.connect(DB_PATH)
    try:
        rows = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        tables = [row[0] for row in rows]
        info["tables"] = tables
        info["table_count"] = len(tables)

        for table in ["history_results", "history_races"]:
            exists = table in tables
            info[f"{table}_exists"] = exists
            if exists:
                count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                info[f"{table}_row_count"] = count
    finally:
        con.close()

    return info


def build_minimal_tables() -> list[dict[str, Any]]:
    return [
        {
            "table_name": "races",
            "phase": "Phase 1 MVP",
            "role": "one row per race",
            "primary_key": ["race_id"],
            "key_policy": {
                "race_id_should_align_with": "canonical_race_key",
                "canonical_race_key": "race_date + venue_id + race_no",
            },
            "suggested_columns": [
                {"name": "race_id", "type": "TEXT", "required": True, "note": "canonical_race_key"},
                {"name": "race_date", "type": "TEXT", "required": True, "note": "YYYYMMDD or ISO date normalized later"},
                {"name": "venue_id", "type": "TEXT", "required": True, "note": "stable venue identifier"},
                {"name": "venue_name", "type": "TEXT", "required": False, "note": "display name"},
                {"name": "race_no", "type": "INTEGER", "required": True, "note": "1-12"},
                {"name": "grade", "type": "TEXT", "required": False, "note": "race grade if available"},
                {"name": "race_type", "type": "TEXT", "required": False, "note": "race type if available"},
                {"name": "distance", "type": "INTEGER", "required": False, "note": "race distance"},
                {"name": "deadline_time", "type": "TEXT", "required": False, "note": "not required for PRE_NIGHT identity"},
                {"name": "created_at", "type": "TEXT", "required": False, "note": "audit timestamp"},
                {"name": "updated_at", "type": "TEXT", "required": False, "note": "audit timestamp"},
            ],
        },
        {
            "table_name": "entries",
            "phase": "Phase 1 MVP",
            "role": "six candidates per race",
            "primary_key": ["race_id", "lane"],
            "key_policy": {
                "canonical_candidate_key": "race_date + venue_id + race_no + lane",
                "race_id": "canonical_race_key",
                "lane": "integer 1-6",
            },
            "suggested_columns": [
                {"name": "race_id", "type": "TEXT", "required": True, "note": "references races.race_id"},
                {"name": "lane", "type": "INTEGER", "required": True, "note": "1-6"},
                {"name": "racer_id", "type": "TEXT", "required": False, "note": "feature or validation field"},
                {"name": "racer_name", "type": "TEXT", "required": False, "note": "not primary key component"},
                {"name": "class", "type": "TEXT", "required": False, "note": "racer class"},
                {"name": "branch", "type": "TEXT", "required": False, "note": "racer branch"},
                {"name": "age", "type": "INTEGER", "required": False, "note": "feature"},
                {"name": "weight", "type": "REAL", "required": False, "note": "feature"},
                {"name": "motor_no", "type": "TEXT", "required": False, "note": "feature, not identity"},
                {"name": "boat_no", "type": "TEXT", "required": False, "note": "feature, not identity"},
                {"name": "entry_source_date", "type": "TEXT", "required": False, "note": "source date"},
                {"name": "created_at", "type": "TEXT", "required": False, "note": "audit timestamp"},
                {"name": "updated_at", "type": "TEXT", "required": False, "note": "audit timestamp"},
            ],
        },
        {
            "table_name": "feature_sets",
            "phase": "Phase 1 MVP",
            "role": "metadata for generated feature files",
            "primary_key": ["feature_set_id"],
            "key_policy": {
                "race_id": "canonical_race_key",
                "stage": "PRE_NIGHT first",
            },
            "suggested_columns": [
                {"name": "feature_set_id", "type": "TEXT", "required": True, "note": "primary key"},
                {"name": "race_id", "type": "TEXT", "required": True, "note": "references races.race_id"},
                {"name": "stage", "type": "TEXT", "required": True, "note": "PRE_NIGHT initially"},
                {"name": "as_of_time", "type": "TEXT", "required": True, "note": "data cutoff time"},
                {"name": "feature_version", "type": "TEXT", "required": True, "note": "feature version"},
                {"name": "has_weather", "type": "INTEGER", "required": False, "note": "0 for PRE_NIGHT"},
                {"name": "has_odds", "type": "INTEGER", "required": False, "note": "0 for PRE_NIGHT"},
                {"name": "has_exhibition", "type": "INTEGER", "required": False, "note": "0 for PRE_NIGHT"},
                {"name": "feature_hash", "type": "TEXT", "required": False, "note": "feature file hash"},
                {"name": "feature_file_path", "type": "TEXT", "required": False, "note": "feature file path"},
                {"name": "feature_summary_json", "type": "TEXT", "required": False, "note": "summary JSON"},
                {"name": "created_at", "type": "TEXT", "required": False, "note": "audit timestamp"},
            ],
        },
        {
            "table_name": "prediction_runs",
            "phase": "Phase 1 MVP",
            "role": "one prediction execution per race, stage, model, feature, and code version",
            "primary_key": ["prediction_run_id"],
            "key_policy": {
                "race_id": "canonical_race_key",
                "stage": "PRE_NIGHT first",
            },
            "suggested_columns": [
                {"name": "prediction_run_id", "type": "TEXT", "required": True, "note": "primary key"},
                {"name": "race_id", "type": "TEXT", "required": True, "note": "references races.race_id"},
                {"name": "stage", "type": "TEXT", "required": True, "note": "PRE_NIGHT initially"},
                {"name": "predicted_at", "type": "TEXT", "required": True, "note": "prediction timestamp"},
                {"name": "data_cutoff_at", "type": "TEXT", "required": True, "note": "prevents future leakage"},
                {"name": "model_version", "type": "TEXT", "required": True, "note": "model version"},
                {"name": "feature_version", "type": "TEXT", "required": True, "note": "feature version"},
                {"name": "code_version", "type": "TEXT", "required": False, "note": "git commit or tag"},
                {"name": "input_data_hash", "type": "TEXT", "required": False, "note": "input hash"},
                {"name": "feature_set_id", "type": "TEXT", "required": False, "note": "references feature_sets"},
                {"name": "has_weather", "type": "INTEGER", "required": False, "note": "0 for PRE_NIGHT"},
                {"name": "has_odds", "type": "INTEGER", "required": False, "note": "0 for PRE_NIGHT"},
                {"name": "has_exhibition", "type": "INTEGER", "required": False, "note": "0 for PRE_NIGHT"},
                {"name": "status", "type": "TEXT", "required": False, "note": "success or failed"},
                {"name": "message", "type": "TEXT", "required": False, "note": "status message"},
                {"name": "created_at", "type": "TEXT", "required": False, "note": "audit timestamp"},
            ],
        },
        {
            "table_name": "predictions",
            "phase": "Phase 1 MVP",
            "role": "predicted probabilities and later expected value fields",
            "primary_key": ["prediction_id"],
            "key_policy": {
                "candidate_level_prediction": "race_id + lane",
                "combination_prediction": "race_id + bet_type + combination",
                "stage": "PRE_NIGHT first",
            },
            "suggested_columns": [
                {"name": "prediction_id", "type": "TEXT", "required": True, "note": "primary key"},
                {"name": "prediction_run_id", "type": "TEXT", "required": True, "note": "references prediction_runs"},
                {"name": "race_id", "type": "TEXT", "required": True, "note": "references races.race_id"},
                {"name": "stage", "type": "TEXT", "required": True, "note": "PRE_NIGHT initially"},
                {"name": "lane", "type": "INTEGER", "required": False, "note": "for candidate-level probabilities"},
                {"name": "bet_type", "type": "TEXT", "required": True, "note": "win, quinella, trifecta, etc."},
                {"name": "combination", "type": "TEXT", "required": False, "note": "for combination bets"},
                {"name": "predicted_probability", "type": "REAL", "required": True, "note": "model output"},
                {"name": "odds", "type": "REAL", "required": False, "note": "null for PRE_NIGHT"},
                {"name": "expected_value", "type": "REAL", "required": False, "note": "null for PRE_NIGHT initially"},
                {"name": "recommended_stake", "type": "INTEGER", "required": False, "note": "null until recommendation phase"},
                {"name": "rank", "type": "INTEGER", "required": False, "note": "ranking within race/bet_type"},
                {"name": "is_recommended", "type": "INTEGER", "required": False, "note": "0 or null for early preview"},
                {"name": "confidence", "type": "TEXT", "required": False, "note": "display confidence"},
                {"name": "created_at", "type": "TEXT", "required": False, "note": "audit timestamp"},
            ],
        },
        {
            "table_name": "results",
            "phase": "Phase 1 MVP",
            "role": "race result by race_id and lane",
            "primary_key": ["race_id", "lane"],
            "key_policy": {
                "race_id": "canonical_race_key",
                "lane": "integer 1-6",
            },
            "suggested_columns": [
                {"name": "race_id", "type": "TEXT", "required": True, "note": "references races.race_id"},
                {"name": "lane", "type": "INTEGER", "required": True, "note": "1-6"},
                {"name": "finish_position", "type": "INTEGER", "required": False, "note": "result"},
                {"name": "course", "type": "INTEGER", "required": False, "note": "actual course"},
                {"name": "start_timing", "type": "REAL", "required": False, "note": "result ST"},
                {"name": "decided_by", "type": "TEXT", "required": False, "note": "winning method"},
                {"name": "disqualified", "type": "INTEGER", "required": False, "note": "0 or 1"},
                {"name": "created_at", "type": "TEXT", "required": False, "note": "audit timestamp"},
            ],
        },
        {
            "table_name": "payouts",
            "phase": "Phase 1 MVP",
            "role": "payout by race, bet type, and combination",
            "primary_key": ["race_id", "bet_type", "combination"],
            "key_policy": {
                "race_id": "canonical_race_key",
                "combination": "bet-specific combination string",
            },
            "suggested_columns": [
                {"name": "race_id", "type": "TEXT", "required": True, "note": "references races.race_id"},
                {"name": "bet_type", "type": "TEXT", "required": True, "note": "bet type"},
                {"name": "combination", "type": "TEXT", "required": True, "note": "winning combination"},
                {"name": "payout", "type": "INTEGER", "required": False, "note": "payout per 100 yen"},
                {"name": "popularity", "type": "INTEGER", "required": False, "note": "result popularity"},
                {"name": "created_at", "type": "TEXT", "required": False, "note": "audit timestamp"},
            ],
        },
        {
            "table_name": "stage_metrics",
            "phase": "Phase 1 MVP",
            "role": "aggregated evaluation metrics by stage and period",
            "primary_key": ["id"],
            "key_policy": {
                "stage": "PRE_NIGHT first",
                "period": "daily, weekly, or monthly aggregation",
            },
            "suggested_columns": [
                {"name": "id", "type": "INTEGER", "required": True, "note": "autoincrement primary key"},
                {"name": "evaluated_at", "type": "TEXT", "required": True, "note": "evaluation timestamp"},
                {"name": "period", "type": "TEXT", "required": True, "note": "evaluation period"},
                {"name": "stage", "type": "TEXT", "required": True, "note": "PRE_NIGHT initially"},
                {"name": "model_version", "type": "TEXT", "required": False, "note": "model version"},
                {"name": "bet_type", "type": "TEXT", "required": False, "note": "bet type"},
                {"name": "races_count", "type": "INTEGER", "required": False, "note": "evaluated race count"},
                {"name": "bets_count", "type": "INTEGER", "required": False, "note": "evaluated bet count"},
                {"name": "hit_count", "type": "INTEGER", "required": False, "note": "hit count"},
                {"name": "hit_rate", "type": "REAL", "required": False, "note": "hit rate"},
                {"name": "total_stake", "type": "INTEGER", "required": False, "note": "total stake"},
                {"name": "total_payout", "type": "INTEGER", "required": False, "note": "total payout"},
                {"name": "profit", "type": "INTEGER", "required": False, "note": "profit"},
                {"name": "roi", "type": "REAL", "required": False, "note": "return on investment"},
                {"name": "logloss", "type": "REAL", "required": False, "note": "log loss"},
                {"name": "brier_score", "type": "REAL", "required": False, "note": "Brier score"},
                {"name": "created_at", "type": "TEXT", "required": False, "note": "audit timestamp"},
            ],
        },
    ]


def main() -> None:
    config = load_json(CONFIG_PATH)

    if not isinstance(config, dict):
        fail(f"{CONFIG_PATH} must contain JSON object")

    if config.get("enabled") is not False:
        fail(f"history feature config must remain enabled:false, got {config.get('enabled')!r}")

    if not PREDICTION_PATH.exists():
        fail(f"missing file: {PREDICTION_PATH}")

    existing_db = inspect_existing_database()

    minimal_tables = build_minimal_tables()
    minimal_table_names = [table["table_name"] for table in minimal_tables]

    optional_early_tables = [
        {
            "table_name": "model_registry",
            "role": "track model versions and active model",
            "reason": "useful once PRE_NIGHT model training begins",
        },
        {
            "table_name": "training_runs",
            "role": "track training execution and metrics",
            "reason": "useful for reproducibility after model training begins",
        },
        {
            "table_name": "ingestion_runs",
            "role": "track data ingestion status and source logs",
            "reason": "useful once program/result ingestion is implemented",
        },
    ]

    deferred_tables = [
        {
            "table_name": "weather_water_snapshots",
            "deferred_until": "Phase 2 MORNING or later",
            "reason": "PRE_NIGHT must not use same-day weather or water information",
        },
        {
            "table_name": "exhibition_snapshots",
            "deferred_until": "Phase 3 POST_EXHIBITION",
            "reason": "exhibition data is unavailable for PRE_NIGHT",
        },
        {
            "table_name": "odds_snapshots",
            "deferred_until": "Phase 4 odds and expected value",
            "reason": "PRE_NIGHT must not use same-day odds",
        },
        {
            "table_name": "prediction_changes",
            "deferred_until": "stage comparison after multiple stages exist",
            "reason": "requires MORNING, POST_EXHIBITION, or FINAL predictions",
        },
        {
            "table_name": "stage_transition_metrics",
            "deferred_until": "Phase 5 continuous improvement",
            "reason": "requires multiple stages and enough evaluation history",
        },
        {
            "table_name": "racer_stats_snapshot",
            "deferred_until": "after minimal PRE_NIGHT flow is defined",
            "reason": "can be introduced as feature source table after schema preview",
        },
        {
            "table_name": "motor_boat_stats_snapshot",
            "deferred_until": "after minimal PRE_NIGHT flow is defined",
            "reason": "can be introduced as feature source table after schema preview",
        },
        {
            "table_name": "venue_bias_daily",
            "deferred_until": "after minimal PRE_NIGHT flow is defined",
            "reason": "can be introduced as feature source table after schema preview",
        },
    ]

    pre_night_forbidden_information = [
        "same-day odds",
        "exhibition_time",
        "exhibition_st",
        "exhibition_course",
        "same-day wind_speed",
        "same-day wave_height",
        "same-day weather snapshots not available at previous night",
        "results",
        "payouts",
        "final odds",
        "popularity after market movement",
    ]

    result = {
        "step": "STEP150-B",
        "preview_type": "phase1-mvp-db-schema",
        "connection_mode": "design-only",
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
        "source_files": {
            "history_feature_config": str(CONFIG_PATH),
            "prediction_json": str(PREDICTION_PATH),
            "schema_sql": str(SCHEMA_SQL_PATH),
            "database": str(DB_PATH),
        },
        "output_file": str(OUTPUT_PATH),
        "canonical_keys": {
            "canonical_race_key": {
                "components": ["race_date", "venue_id", "race_no"],
                "recommended_format": "race_date + '_' + venue_id + '_' + race_no",
                "purpose": "stable race identity",
            },
            "canonical_candidate_key": {
                "components": ["race_date", "venue_id", "race_no", "lane"],
                "recommended_format": "race_date + '_' + venue_id + '_' + race_no + '_' + lane",
                "purpose": "stable candidate identity",
            },
        },
        "existing_database_inspection": existing_db,
        "phase1_mvp_goal": [
            "ingest race/program data",
            "store races and entries",
            "generate PRE_NIGHT features",
            "run PRE_NIGHT prediction",
            "store predictions",
            "later ingest results",
            "evaluate PRE_NIGHT performance",
        ],
        "minimal_tables": minimal_tables,
        "minimal_table_names": minimal_table_names,
        "minimal_table_count": len(minimal_table_names),
        "optional_early_tables": optional_early_tables,
        "optional_early_table_names": [table["table_name"] for table in optional_early_tables],
        "deferred_tables": deferred_tables,
        "deferred_table_names": [table["table_name"] for table in deferred_tables],
        "pre_night_forbidden_information": pre_night_forbidden_information,
        "safety_decision": {
            "do_not_enable_history_features": True,
            "do_not_connect_prediction_core": True,
            "do_not_modify_prediction_json": True,
            "do_not_modify_schema_sql": True,
            "do_not_modify_database": True,
            "do_not_create_tables_in_step150b": True,
            "do_not_change_prediction_scores": True,
            "do_not_change_ranks": True,
            "do_not_change_recommendations": True,
            "do_not_change_expected_values": True,
        },
        "next_step": {
            "step": "STEP150-C",
            "purpose": "add a checker for this Phase 1 MVP DB schema preview",
        },
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("Phase 1 MVP DB schema preview export: OK")
    print("STEP 150-B CHECK: OK")
    print(f"output={OUTPUT_PATH}")
    print("preview_type=phase1-mvp-db-schema")
    print("connection_mode=design-only")
    print("config_enabled=False")
    print("history_features_enabled=False")
    print("prediction_core_connected=False")
    print("modifies_prediction_json=False")
    print("writes_prediction_json=False")
    print("writes_schema_sql=False")
    print("writes_database=False")
    print("creates_tables=False")
    print(f"minimal_table_count={len(minimal_table_names)}")
    print("minimal_tables=" + ",".join(minimal_table_names))


if __name__ == "__main__":
    main()
