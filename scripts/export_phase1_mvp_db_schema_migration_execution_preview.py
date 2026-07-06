#!/usr/bin/env python3
"""
STEP155-B: Export Phase 1 MVP DB schema migration execution-mode preview.

This exporter creates:
- docs/phase1_mvp_db_schema_migration_execution_preview.json

Important:
- This is execution-preview-only.
- It does not execute migration.
- It does not execute DDL.
- It does not modify db/schema.sql.
- It does not modify db/boatrace.sqlite3.
- It does not modify docs/prediction.json.
- It does not enable data/history_feature_config.json.
- It does not modify scripts/migrate_phase1_mvp_db_schema.py.
"""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OUTPUT_PATH = Path("docs/phase1_mvp_db_schema_migration_execution_preview.json")

DRAFT_SCRIPT_PATH = Path("scripts/migrate_phase1_mvp_db_schema.py")
DRAFT_CHECKER_PATH = Path("scripts/check_phase1_mvp_db_schema_migration_draft.py")
MIGRATION_SCRIPT_PREVIEW_PATH = Path("docs/phase1_mvp_db_schema_migration_script_preview.json")
DDL_PREVIEW_PATH = Path("docs/phase1_mvp_db_schema_ddl_preview.json")
CONFIG_PATH = Path("data/history_feature_config.json")
PREDICTION_PATH = Path("docs/prediction.json")
SCHEMA_SQL_PATH = Path("db/schema.sql")
DB_PATH = Path("db/boatrace.sqlite3")

STEP155A_DIR = Path("/tmp/history_feature_155a")

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

PROTECTED_DIFF_PATHS = [
    DRAFT_SCRIPT_PATH,
    DRAFT_CHECKER_PATH,
    MIGRATION_SCRIPT_PREVIEW_PATH,
    DDL_PREVIEW_PATH,
    SCHEMA_SQL_PATH,
    DB_PATH,
    PREDICTION_PATH,
    CONFIG_PATH,
    Path("README.md"),
    Path("docs/phase1-mvp-db-schema-migration-draft.md"),
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
    "same-day weather",
    "same-day water condition",
    "confirmed race outcome",
    "results",
    "payouts",
    "post-race information",
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


def sha256_file(path: Path) -> str:
    require_file(path)
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_diff_modified(path: Path) -> bool:
    result = subprocess.run(
        ["git", "diff", "--quiet", "--", str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode != 0


def require_not_modified(path: Path) -> None:
    require_file(path)
    if git_diff_modified(path):
        fail(f"protected file has uncommitted diff: {path}")


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


def extract_assignment_from_ast(script_path: Path, name: str) -> Any:
    require_file(script_path)
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


def audit_ddl_candidates() -> dict[str, Any]:
    ddl_candidates = extract_assignment_from_ast(DRAFT_SCRIPT_PATH, "DDL_CANDIDATES")

    if not isinstance(ddl_candidates, dict):
        fail("DDL_CANDIDATES must be a dict")

    actual_tables = list(ddl_candidates.keys())
    if actual_tables != REQUIRED_MINIMAL_TABLES:
        fail(f"DDL_CANDIDATES table order mismatch: {actual_tables!r}")

    table_audits: list[dict[str, Any]] = []
    danger_hits: list[dict[str, Any]] = []

    for table_name in REQUIRED_MINIMAL_TABLES:
        ddl = ddl_candidates.get(table_name)
        if not isinstance(ddl, str):
            fail(f"DDL_CANDIDATES[{table_name!r}] must be a string")

        ddl_upper = ddl.upper()
        has_create_table_if_not_exists = "CREATE TABLE IF NOT EXISTS" in ddl_upper
        hits = [pattern for pattern in FORBIDDEN_SQL_PATTERNS if pattern in ddl_upper]

        if not has_create_table_if_not_exists:
            fail(f"{table_name} DDL missing CREATE TABLE IF NOT EXISTS")

        if hits:
            danger_hits.append({"table": table_name, "patterns": hits})

        table_audits.append(
            {
                "table": table_name,
                "has_create_table_if_not_exists": has_create_table_if_not_exists,
                "danger_hits": hits,
                "candidate_statement_type": "CREATE TABLE IF NOT EXISTS",
            }
        )

    if danger_hits:
        fail(f"danger patterns found in DDL_CANDIDATES: {danger_hits!r}")

    return {
        "table_count": len(actual_tables),
        "tables": actual_tables,
        "table_audits": table_audits,
        "danger_pattern_count": len(danger_hits),
        "danger_patterns": "NONE",
        "ddl_candidates_audit_ok": True,
    }


def run_command_capture(command: list[str]) -> dict[str, Any]:
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return {
        "command": command,
        "returncode": result.returncode,
        "output": result.stdout,
    }


def validate_draft_script_runtime() -> dict[str, Any]:
    result = run_command_capture(["python", str(DRAFT_SCRIPT_PATH)])
    output = result["output"]

    if result["returncode"] != 0:
        fail(f"draft script failed with rc={result['returncode']}\n{output}")

    required_lines = [
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

    missing = [line for line in required_lines if line not in output]
    if missing:
        fail(f"draft script output missing required lines: {missing!r}")

    for marker in ["ERROR:", "FAILED", "Traceback", "PermissionError", "TypeError"]:
        if marker in output:
            fail(f"draft script output contains error marker: {marker}")

    return {
        "draft_runtime_ok": True,
        "returncode": result["returncode"],
        "required_lines_present": required_lines,
    }


def validate_draft_checker_runtime() -> dict[str, Any]:
    result = run_command_capture(["python", str(DRAFT_CHECKER_PATH)])
    output = result["output"]

    if result["returncode"] != 0:
        fail(f"draft checker failed with rc={result['returncode']}\n{output}")

    required_lines = [
        "Phase 1 MVP DB schema migration draft validation: OK",
        "STEP 154-C CHECK: OK",
        "mode=dry-run",
        "executes_ddl=False",
        "writes_database=False",
        "writes_schema_sql=False",
        "runs_migration=False",
        "minimal_table_count=8",
        "danger_pattern_count=0",
        "danger_patterns=NONE",
    ]

    missing = [line for line in required_lines if line not in output]
    if missing:
        fail(f"draft checker output missing required lines: {missing!r}")

    for marker in ["ERROR:", "FAILED", "Traceback", "PermissionError", "TypeError"]:
        if marker in output:
            fail(f"draft checker output contains error marker: {marker}")

    return {
        "draft_checker_ok": True,
        "returncode": result["returncode"],
        "required_lines_present": required_lines,
    }


def validate_previous_previews() -> dict[str, Any]:
    migration_preview = load_json(MIGRATION_SCRIPT_PREVIEW_PATH)
    ddl_preview = load_json(DDL_PREVIEW_PATH)

    if migration_preview.get("step") != "STEP153-B":
        fail(f"migration script preview step must be STEP153-B, got {migration_preview.get('step')!r}")

    if migration_preview.get("preview_type") != "phase1-mvp-db-schema-migration-script-preview":
        fail("migration script preview_type mismatch")

    if migration_preview.get("connection_mode") != "migration-preview-only":
        fail("migration script preview connection_mode mismatch")

    if migration_preview.get("migration_script_preview_only") is not True:
        fail("migration_script_preview_only must be True")

    if migration_preview.get("migration_script_execution_mode") != "not-created-not-executed":
        fail("migration_script_execution_mode must be not-created-not-executed")

    if migration_preview.get("ddl_execution_mode") != "not-executed":
        fail("migration preview ddl_execution_mode must be not-executed")

    if migration_preview.get("minimal_table_count") != 8:
        fail("migration preview minimal_table_count must be 8")

    if migration_preview.get("minimal_tables") != REQUIRED_MINIMAL_TABLES:
        fail("migration preview minimal_tables mismatch")

    if ddl_preview.get("step") != "STEP152-B":
        fail(f"DDL preview step must be STEP152-B, got {ddl_preview.get('step')!r}")

    if ddl_preview.get("preview_type") != "phase1-mvp-db-schema-ddl-preview":
        fail("DDL preview preview_type mismatch")

    if ddl_preview.get("connection_mode") != "ddl-preview-only":
        fail("DDL preview connection_mode mismatch")

    if ddl_preview.get("ddl_execution_mode") != "not-executed":
        fail("DDL preview ddl_execution_mode must be not-executed")

    if ddl_preview.get("minimal_table_count") != 8:
        fail("DDL preview minimal_table_count must be 8")

    return {
        "migration_script_preview": {
            "path": str(MIGRATION_SCRIPT_PREVIEW_PATH),
            "step": migration_preview.get("step"),
            "preview_type": migration_preview.get("preview_type"),
            "connection_mode": migration_preview.get("connection_mode"),
            "migration_script_preview_only": migration_preview.get("migration_script_preview_only"),
            "migration_script_execution_mode": migration_preview.get("migration_script_execution_mode"),
            "ddl_execution_mode": migration_preview.get("ddl_execution_mode"),
            "minimal_table_count": migration_preview.get("minimal_table_count"),
        },
        "ddl_preview": {
            "path": str(DDL_PREVIEW_PATH),
            "step": ddl_preview.get("step"),
            "preview_type": ddl_preview.get("preview_type"),
            "connection_mode": ddl_preview.get("connection_mode"),
            "ddl_execution_mode": ddl_preview.get("ddl_execution_mode"),
            "ddl_preview_only": ddl_preview.get("ddl_preview_only"),
            "minimal_table_count": ddl_preview.get("minimal_table_count"),
        },
    }


def inspect_step155a_logs() -> dict[str, Any]:
    expected_files = [
        STEP155A_DIR / "check_phase1_mvp_db_schema_migration_draft.log",
        STEP155A_DIR / "check_history_database_readiness.log",
        STEP155A_DIR / "migrate_phase1_mvp_db_schema_dry_run.log",
        STEP155A_DIR / "ddl_candidates_audit.log",
        STEP155A_DIR / "dry_run_execution_feasibility_policy.txt",
        STEP155A_DIR / "dry_run_execution_rollback_policy.txt",
        STEP155A_DIR / "step155a_summary.txt",
    ]

    existing = [str(p) for p in expected_files if p.exists()]
    missing = [str(p) for p in expected_files if not p.exists()]

    combined_text = ""
    for p in expected_files:
        if p.exists():
            combined_text += "\n" + p.read_text(encoding="utf-8", errors="replace")

    required_markers = [
        "STEP 154-C CHECK: OK",
        "STEP 154-B CHECK: OK",
        "History database readiness validation: OK",
        "DDL_CANDIDATES audit: OK",
        "table_count=8",
        "danger_pattern_count=0",
        "audit-only",
        "future execution",
    ]

    missing_markers = [marker for marker in required_markers if marker not in combined_text]

    return {
        "step155a_directory": str(STEP155A_DIR),
        "expected_files_present": len(missing) == 0,
        "existing_files": existing,
        "missing_files": missing,
        "required_markers_present": len(missing_markers) == 0,
        "missing_markers": missing_markers,
    }


def protected_file_hashes() -> dict[str, str]:
    return {
        str(SCHEMA_SQL_PATH): sha256_file(SCHEMA_SQL_PATH),
        str(DB_PATH): sha256_file(DB_PATH),
        str(PREDICTION_PATH): sha256_file(PREDICTION_PATH),
        str(CONFIG_PATH): sha256_file(CONFIG_PATH),
    }


def validate_config_disabled() -> None:
    config = load_json(CONFIG_PATH)
    if bool(config.get("enabled", False)):
        fail("data/history_feature_config.json enabled must remain false")


def main() -> None:
    required_paths = [
        DRAFT_SCRIPT_PATH,
        DRAFT_CHECKER_PATH,
        MIGRATION_SCRIPT_PREVIEW_PATH,
        DDL_PREVIEW_PATH,
        CONFIG_PATH,
        PREDICTION_PATH,
        SCHEMA_SQL_PATH,
        DB_PATH,
    ]

    for path in required_paths:
        require_file(path)

    validate_config_disabled()

    for path in PROTECTED_DIFF_PATHS:
        require_not_modified(path)

    previous_preview_validation = validate_previous_previews()
    ddl_candidates_audit = audit_ddl_candidates()
    draft_runtime_validation = validate_draft_script_runtime()
    draft_checker_validation = validate_draft_checker_runtime()
    step155a_log_inspection = inspect_step155a_logs()

    if ddl_candidates_audit["table_count"] != 8:
        fail("DDL_CANDIDATES table_count must be 8")

    if ddl_candidates_audit["danger_pattern_count"] != 0:
        fail("DDL_CANDIDATES danger_pattern_count must be 0")

    preview = {
        "step": "STEP155-B",
        "preview_type": "phase1-mvp-db-schema-migration-execution-preview",
        "connection_mode": "execution-preview-only",
        "safe_mode": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "output": str(OUTPUT_PATH),
        "source_files": {
            "draft_script": str(DRAFT_SCRIPT_PATH),
            "draft_checker": str(DRAFT_CHECKER_PATH),
            "migration_script_preview": str(MIGRATION_SCRIPT_PREVIEW_PATH),
            "ddl_preview": str(DDL_PREVIEW_PATH),
            "config": str(CONFIG_PATH),
            "prediction_json": str(PREDICTION_PATH),
            "schema_sql": str(SCHEMA_SQL_PATH),
            "sqlite_database": str(DB_PATH),
            "step155a_audit_directory": str(STEP155A_DIR),
        },
        "execution_preview_only": True,
        "migration_execution_mode": "not-executed",
        "ddl_execution_mode": "not-executed",
        "executes_ddl": False,
        "writes_database": False,
        "writes_schema_sql": False,
        "creates_tables": False,
        "alters_tables": False,
        "drops_tables": False,
        "runs_migration": False,
        "modifies_prediction_json": False,
        "writes_prediction_json": False,
        "prediction_core_connected": False,
        "config_enabled": False,
        "history_features_enabled": False,
        "minimal_table_count": 8,
        "minimal_tables": REQUIRED_MINIMAL_TABLES,
        "implementation_order": REQUIRED_MINIMAL_TABLES,
        "draft_alignment": {
            "draft_script": str(DRAFT_SCRIPT_PATH),
            "draft_mode": "dry-run",
            "draft_step": "STEP154-B",
            "draft_checker": "STEP154-C",
            "draft_runtime_validation": draft_runtime_validation,
            "draft_checker_validation": draft_checker_validation,
            "ddl_candidates_audit": ddl_candidates_audit,
        },
        "future_execution_mode_requirements": {
            "explicit_execution_flag_required": True,
            "default_mode_must_remain_dry_run": True,
            "clean_git_status_required": True,
            "sqlite_backup_required": True,
            "protected_file_hash_record_required": True,
            "readiness_checks_required": True,
            "create_table_if_not_exists_only": True,
            "future_candidate_statement": "CREATE TABLE IF NOT EXISTS",
            "destructive_sql_forbidden": True,
            "preserve_history_tables": True,
            "history_tables_to_preserve": ["history_races", "history_results"],
            "prediction_json_write_forbidden": True,
            "config_enablement_forbidden": True,
            "prediction_core_connection_forbidden": True,
            "automatic_betting_forbidden": True,
            "execution_must_be_separate_explicit_step": True,
        },
        "forbidden_sql_patterns": FORBIDDEN_SQL_PATTERNS,
        "rollback_requirements": {
            "sqlite_backup_required": True,
            "backup_target": str(DB_PATH),
            "record_sha256_files": [
                str(SCHEMA_SQL_PATH),
                str(DB_PATH),
                str(PREDICTION_PATH),
                str(CONFIG_PATH),
            ],
            "restore_sqlite_backup": True,
            "git_restore_tracked_files": True,
            "record_git_status_before_execution": True,
            "record_commit_hash_before_execution": True,
            "record_sqlite_table_list_before_execution": True,
            "record_row_counts_before_execution": True,
            "do_not_drop_history_races": True,
            "do_not_drop_history_results": True,
        },
        "protected_file_hashes_for_preview": protected_file_hashes(),
        "key_policy": {
            "race_id_policy": "race_id = canonical_race_key",
            "canonical_race_key": 'race_date + "_" + venue_id + "_" + race_no',
            "canonical_candidate_key_policy": 'canonical_candidate_key = race_id + "_" + lane',
            "canonical_candidate_key": 'race_id + "_" + lane',
        },
        "pdf_operation_constraints": {
            "no_automatic_betting": True,
            "collection_interval_policy": "5 to 15 minutes",
            "sqlite_commit_policy": "nightly SQLite merge",
            "llm_usage_policy": "LLM not used for normal prediction",
            "smartphone_centric_operation": True,
        },
        "final_design_pdf_compatibility": {
            "phase1_is_safe_subset_of_final_design": True,
            "deferred_final_design_tables": DEFERRED_FINAL_DESIGN_TABLES,
            "deferred_tables_not_created_in_step155_b": True,
        },
        "pre_night_safety_constraints": {
            "pre_night_only": True,
            "results_and_payouts_allowed_as_pre_night_inputs": False,
            "forbidden_information": PRE_NIGHT_FORBIDDEN_INFORMATION,
        },
        "previous_preview_validation": previous_preview_validation,
        "step155a_audit_reference": step155a_log_inspection,
        "safety_decisions": {
            "do_not_modify_draft_script_in_step155_b": True,
            "do_not_modify_checker_in_step155_b": True,
            "do_not_modify_readiness_scripts_in_step155_b": True,
            "do_not_modify_schema_sql_in_step155_b": True,
            "do_not_modify_sqlite_db_in_step155_b": True,
            "do_not_modify_prediction_json_in_step155_b": True,
            "do_not_enable_history_features_in_step155_b": True,
            "do_not_connect_prediction_core_in_step155_b": True,
            "do_not_execute_migration_in_step155_b": True,
            "do_not_execute_ddl_in_step155_b": True,
        },
        "next_step": {
            "step": "STEP155-C",
            "description": "Create checker for Phase 1 MVP DB schema migration execution preview JSON.",
            "must_not_execute_migration": True,
        },
    }

    required_false_flags = [
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

    for flag in required_false_flags:
        if preview.get(flag) is not False:
            fail(f"{flag} must be False")

    if preview["execution_preview_only"] is not True:
        fail("execution_preview_only must be True")

    if preview["minimal_table_count"] != 8:
        fail("minimal_table_count must be 8")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(preview, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print("Phase 1 MVP DB schema migration execution preview export: OK")
    print("STEP 155-B CHECK: OK")
    print(f"preview_type={preview['preview_type']}")
    print(f"connection_mode={preview['connection_mode']}")
    print(f"execution_preview_only={preview['execution_preview_only']}")
    print(f"migration_execution_mode={preview['migration_execution_mode']}")
    print(f"ddl_execution_mode={preview['ddl_execution_mode']}")
    print(f"executes_ddl={preview['executes_ddl']}")
    print(f"writes_database={preview['writes_database']}")
    print(f"writes_schema_sql={preview['writes_schema_sql']}")
    print(f"creates_tables={preview['creates_tables']}")
    print(f"alters_tables={preview['alters_tables']}")
    print(f"drops_tables={preview['drops_tables']}")
    print(f"runs_migration={preview['runs_migration']}")
    print(f"modifies_prediction_json={preview['modifies_prediction_json']}")
    print(f"writes_prediction_json={preview['writes_prediction_json']}")
    print(f"prediction_core_connected={preview['prediction_core_connected']}")
    print(f"config_enabled={preview['config_enabled']}")
    print(f"history_features_enabled={preview['history_features_enabled']}")
    print(f"minimal_table_count={preview['minimal_table_count']}")
    print(f"draft_script={preview['draft_alignment']['draft_script']}")
    print(f"draft_mode={preview['draft_alignment']['draft_mode']}")
    print(f"ddl_candidates_table_count={ddl_candidates_audit['table_count']}")
    print(f"ddl_candidates_danger_pattern_count={ddl_candidates_audit['danger_pattern_count']}")


if __name__ == "__main__":
    main()
