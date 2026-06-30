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
EXPORTER_PATH = Path("scripts/export_phase1_mvp_db_schema_preview.py")
PREVIEW_PATH = Path("docs/phase1_mvp_db_schema_preview.json")


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

OPTIONAL_EARLY_TABLES = [
    "model_registry",
    "training_runs",
    "ingestion_runs",
]

DEFERRED_TABLES = [
    "weather_water_snapshots",
    "exhibition_snapshots",
    "odds_snapshots",
    "prediction_changes",
    "stage_transition_metrics",
    "racer_stats_snapshot",
    "motor_boat_stats_snapshot",
    "venue_bias_daily",
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


def require_name_set(actual: list[Any], expected: list[str], label: str) -> None:
    if not all(isinstance(item, str) for item in actual):
        fail(f"{label} must contain only strings")

    missing = [name for name in expected if name not in actual]
    if missing:
        fail(f"{label} missing required names: {missing}")

    extra = [name for name in actual if name not in expected]
    if extra:
        fail(f"{label} contains unexpected names: {extra}")


def require_table_objects(tables: list[Any], expected_names: list[str], label: str) -> None:
    if not all(isinstance(item, dict) for item in tables):
        fail(f"{label} must contain only objects")

    names = []
    for index, table in enumerate(tables):
        name = table.get("table_name")
        if not isinstance(name, str) or not name:
            fail(f"{label}[{index}].table_name must be non-empty string")
        names.append(name)

        role = table.get("role")
        if not isinstance(role, str) or not role:
            fail(f"{label}[{index}].role must be non-empty string")

        primary_key = table.get("primary_key")
        if not isinstance(primary_key, list) or not primary_key:
            fail(f"{label}[{index}].primary_key must be non-empty list")

        suggested_columns = table.get("suggested_columns")
        if not isinstance(suggested_columns, list) or not suggested_columns:
            fail(f"{label}[{index}].suggested_columns must be non-empty list")

    missing = [name for name in expected_names if name not in names]
    if missing:
        fail(f"{label} missing table objects: {missing}")

def require_named_preview_objects(tables: list[Any], expected_names: list[str], label: str) -> None:
    if not all(isinstance(item, dict) for item in tables):
        fail(f"{label} must contain only objects")

    names = []
    for index, table in enumerate(tables):
        name = table.get("table_name")
        if not isinstance(name, str) or not name:
            fail(f"{label}[{index}].table_name must be non-empty string")
        names.append(name)

        has_role = isinstance(table.get("role"), str) and bool(table.get("role"))
        has_reason = isinstance(table.get("reason"), str) and bool(table.get("reason"))
        has_deferred_until = isinstance(table.get("deferred_until"), str) and bool(table.get("deferred_until"))

        if not (has_role or has_reason or has_deferred_until):
            fail(f"{label}[{index}] must contain role, reason, or deferred_until")

    missing = [name for name in expected_names if name not in names]
    if missing:
        fail(f"{label} missing table objects: {missing}")


def main() -> None:
    if not EXPORTER_PATH.exists():
        fail(f"missing exporter script: {EXPORTER_PATH}")

    config = load_json(CONFIG_PATH)
    preview = load_json(PREVIEW_PATH)

    if not isinstance(config, dict):
        fail(f"{CONFIG_PATH} must contain JSON object")

    if not isinstance(preview, dict):
        fail(f"{PREVIEW_PATH} must contain JSON object")

    if config.get("enabled") is not False:
        fail(f"data/history_feature_config.json enabled must be False, got {config.get('enabled')!r}")

    require_value(preview, "step", "STEP150-B")
    require_value(preview, "preview_type", "phase1-mvp-db-schema")
    require_value(preview, "connection_mode", "design-only")

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

    source_files = require_dict(preview, "source_files")
    expected_source_files = {
        "history_feature_config": str(CONFIG_PATH),
        "prediction_json": str(PREDICTION_PATH),
        "schema_sql": str(SCHEMA_SQL_PATH),
        "database": str(DB_PATH),
    }

    for key, expected in expected_source_files.items():
        actual = source_files.get(key)
        if actual != expected:
            fail(f"source_files.{key} must be {expected!r}, got {actual!r}")

    output_file = require_key(preview, "output_file")
    if output_file != str(PREVIEW_PATH):
        fail(f"output_file must be {str(PREVIEW_PATH)!r}, got {output_file!r}")

    canonical = require_dict(preview, "canonical_keys")

    race_key = require_dict(canonical, "canonical_race_key")
    race_components = require_list(race_key, "components")
    if race_components != ["race_date", "venue_id", "race_no"]:
        fail(f"canonical_race_key.components mismatch: {race_components!r}")

    candidate_key = require_dict(canonical, "canonical_candidate_key")
    candidate_components = require_list(candidate_key, "components")
    if candidate_components != ["race_date", "venue_id", "race_no", "lane"]:
        fail(f"canonical_candidate_key.components mismatch: {candidate_components!r}")

    existing_db = require_dict(preview, "existing_database_inspection")
    if existing_db.get("db_path") != str(DB_PATH):
        fail(f"existing_database_inspection.db_path must be {str(DB_PATH)!r}, got {existing_db.get('db_path')!r}")

    if existing_db.get("db_exists") is not True:
        fail("existing_database_inspection.db_exists must be True")

    if existing_db.get("history_results_exists") is not True:
        fail("existing_database_inspection.history_results_exists must be True")

    if existing_db.get("history_races_exists") is not True:
        fail("existing_database_inspection.history_races_exists must be True")

    require_list(preview, "phase1_mvp_goal")

    minimal_tables = require_list(preview, "minimal_tables")
    require_table_objects(minimal_tables, REQUIRED_MINIMAL_TABLES, "minimal_tables")

    minimal_names = require_list(preview, "minimal_table_names")
    require_name_set(minimal_names, REQUIRED_MINIMAL_TABLES, "minimal_table_names")

    minimal_count = require_nonnegative_int(preview, "minimal_table_count")
    if minimal_count != len(REQUIRED_MINIMAL_TABLES):
        fail(f"minimal_table_count must be {len(REQUIRED_MINIMAL_TABLES)}, got {minimal_count}")

    optional_early = require_list(preview, "optional_early_tables")
    require_named_preview_objects(optional_early, OPTIONAL_EARLY_TABLES, "optional_early_tables")

    optional_early_names = require_list(preview, "optional_early_table_names")
    require_name_set(optional_early_names, OPTIONAL_EARLY_TABLES, "optional_early_table_names")

    deferred = require_list(preview, "deferred_tables")
    require_named_preview_objects(deferred, DEFERRED_TABLES, "deferred_tables")

    deferred_names = require_list(preview, "deferred_table_names")
    require_name_set(deferred_names, DEFERRED_TABLES, "deferred_table_names")

    forbidden = require_list(preview, "pre_night_forbidden_information")
    required_forbidden = [
        "same-day odds",
        "exhibition_time",
        "exhibition_st",
        "exhibition_course",
        "results",
        "payouts",
    ]
    for item in required_forbidden:
        if item not in forbidden:
            fail(f"pre_night_forbidden_information missing {item!r}")

    safety = require_dict(preview, "safety_decision")
    require_true(safety, "do_not_enable_history_features")
    require_true(safety, "do_not_connect_prediction_core")
    require_true(safety, "do_not_modify_prediction_json")
    require_true(safety, "do_not_modify_schema_sql")
    require_true(safety, "do_not_modify_database")
    require_true(safety, "do_not_create_tables_in_step150b")
    require_true(safety, "do_not_change_prediction_scores")
    require_true(safety, "do_not_change_ranks")
    require_true(safety, "do_not_change_recommendations")
    require_true(safety, "do_not_change_expected_values")

    next_step = require_dict(preview, "next_step")
    if next_step.get("step") != "STEP150-C":
        fail(f"next_step.step must be STEP150-C, got {next_step.get('step')!r}")

    check_no_diff(PREDICTION_PATH, "docs/prediction.json")
    check_no_diff(SCHEMA_SQL_PATH, "db/schema.sql")
    check_no_diff(DB_PATH, "db/boatrace.sqlite3")

    print("Phase 1 MVP DB schema preview validation: OK")
    print("STEP 150-C CHECK: OK")
    print(f"output={PREVIEW_PATH}")
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
    print(f"minimal_table_count={minimal_count}")
    print("minimal_tables=" + ",".join(REQUIRED_MINIMAL_TABLES))
    print("canonical_race_key_components=race_date,venue_id,race_no")
    print("canonical_candidate_key_components=race_date,venue_id,race_no,lane")


if __name__ == "__main__":
    main()
