#!/usr/bin/env python3
"""
STEP156-B: Export Phase 1 MVP DB schema runtime guard preview.

This exporter creates:
- docs/phase1_mvp_db_schema_runtime_guard_preview.json

Important:
- This is runtime-guard-preview-only.
- It does not execute migration.
- It does not execute DDL.
- It does not modify db/schema.sql.
- It does not modify db/boatrace.sqlite3.
- It does not modify docs/prediction.json.
- It does not enable data/history_feature_config.json.
- It does not modify existing scripts/readiness/README/docs markdown.
"""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OUTPUT_PATH = Path("docs/phase1_mvp_db_schema_runtime_guard_preview.json")

DRAFT_SCRIPT_PATH = Path("scripts/migrate_phase1_mvp_db_schema.py")
EXECUTION_PREVIEW_EXPORTER_PATH = Path("scripts/export_phase1_mvp_db_schema_migration_execution_preview.py")
EXECUTION_PREVIEW_CHECKER_PATH = Path("scripts/check_phase1_mvp_db_schema_migration_execution_preview.py")
EXECUTION_PREVIEW_PATH = Path("docs/phase1_mvp_db_schema_migration_execution_preview.json")

MIGRATION_SCRIPT_PREVIEW_PATH = Path("docs/phase1_mvp_db_schema_migration_script_preview.json")
DDL_PREVIEW_PATH = Path("docs/phase1_mvp_db_schema_ddl_preview.json")

CONFIG_PATH = Path("data/history_feature_config.json")
PREDICTION_PATH = Path("docs/prediction.json")
SCHEMA_SQL_PATH = Path("db/schema.sql")
DB_PATH = Path("db/boatrace.sqlite3")
README_PATH = Path("README.md")

STEP156A_DIR = Path("/tmp/history_feature_156a")

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
    EXECUTION_PREVIEW_EXPORTER_PATH,
    EXECUTION_PREVIEW_CHECKER_PATH,
    EXECUTION_PREVIEW_PATH,
    MIGRATION_SCRIPT_PREVIEW_PATH,
    DDL_PREVIEW_PATH,
    SCHEMA_SQL_PATH,
    DB_PATH,
    PREDICTION_PATH,
    CONFIG_PATH,
    README_PATH,
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


def validate_config_disabled() -> None:
    config = load_json(CONFIG_PATH)
    if bool(config.get("enabled", False)):
        fail("data/history_feature_config.json enabled must remain false")


def validate_execution_preview() -> dict[str, Any]:
    data = load_json(EXECUTION_PREVIEW_PATH)

    expected = {
        "step": "STEP155-B",
        "preview_type": "phase1-mvp-db-schema-migration-execution-preview",
        "connection_mode": "execution-preview-only",
        "safe_mode": True,
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
    }

    for key, value in expected.items():
        if data.get(key) != value:
            fail(f"execution preview {key} must be {value!r}, got {data.get(key)!r}")

    if data.get("minimal_tables") != REQUIRED_MINIMAL_TABLES:
        fail("execution preview minimal_tables mismatch")

    draft = data.get("draft_alignment")
    if not isinstance(draft, dict):
        fail("execution preview draft_alignment must be an object")

    if draft.get("draft_mode") != "dry-run":
        fail("execution preview draft_mode must be dry-run")

    ddl_audit = draft.get("ddl_candidates_audit")
    if not isinstance(ddl_audit, dict):
        fail("execution preview ddl_candidates_audit must be an object")

    if ddl_audit.get("table_count") != 8:
        fail("execution preview ddl_candidates_audit.table_count must be 8")

    if ddl_audit.get("danger_pattern_count") != 0:
        fail("execution preview ddl_candidates_audit.danger_pattern_count must be 0")

    return {
        "path": str(EXECUTION_PREVIEW_PATH),
        "step": data.get("step"),
        "preview_type": data.get("preview_type"),
        "connection_mode": data.get("connection_mode"),
        "execution_preview_only": data.get("execution_preview_only"),
        "migration_execution_mode": data.get("migration_execution_mode"),
        "ddl_execution_mode": data.get("ddl_execution_mode"),
        "minimal_table_count": data.get("minimal_table_count"),
        "draft_mode": draft.get("draft_mode"),
        "ddl_candidates_table_count": ddl_audit.get("table_count"),
        "ddl_candidates_danger_pattern_count": ddl_audit.get("danger_pattern_count"),
    }


def validate_execution_checker_runtime() -> dict[str, Any]:
    result = run_command_capture(["python", str(EXECUTION_PREVIEW_CHECKER_PATH)])
    output = result["output"]

    if result["returncode"] != 0:
        fail(f"execution preview checker failed with rc={result['returncode']}\n{output}")

    required_lines = [
        "Phase 1 MVP DB schema migration execution preview validation: OK",
        "STEP 155-C CHECK: OK",
        "execution_preview_only=True",
        "migration_execution_mode=not-executed",
        "ddl_execution_mode=not-executed",
        "executes_ddl=False",
        "writes_database=False",
        "writes_schema_sql=False",
        "runs_migration=False",
        "minimal_table_count=8",
    ]

    missing = [line for line in required_lines if line not in output]
    if missing:
        fail(f"execution checker output missing required lines: {missing!r}")

    for marker in ["ERROR:", "FAILED", "Traceback", "PermissionError", "TypeError"]:
        if marker in output:
            fail(f"execution checker output contains error marker: {marker}")

    return {
        "execution_preview_checker_ok": True,
        "returncode": result["returncode"],
        "required_lines_present": required_lines,
    }


def validate_draft_runtime() -> dict[str, Any]:
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


def inspect_step156a_logs() -> dict[str, Any]:
    expected_files = [
        STEP156A_DIR / "check_phase1_mvp_db_schema_migration_execution_preview.log",
        STEP156A_DIR / "check_history_database_readiness.log",
        STEP156A_DIR / "migrate_phase1_mvp_db_schema_dry_run.log",
        STEP156A_DIR / "execution_preview_safety_fields.txt",
        STEP156A_DIR / "protected_file_hashes.txt",
        STEP156A_DIR / "runtime_guard_policy.txt",
        STEP156A_DIR / "runtime_rollback_policy.txt",
        STEP156A_DIR / "step156a_summary.txt",
    ]

    existing = [str(p) for p in expected_files if p.exists()]
    missing = [str(p) for p in expected_files if not p.exists()]

    combined_text = ""
    for path in expected_files:
        if path.exists():
            combined_text += "\n" + path.read_text(encoding="utf-8", errors="replace")

    required_marker_groups = [
        ["STEP 155-C CHECK: OK"],
        ["STEP 154-C CHECK: OK"],
        ["STEP 154-B CHECK: OK"],
        ["History database readiness validation: OK"],
        ["execution_preview_only=True"],
        ["migration_execution_mode=not-executed", "migration_execution_mode='not-executed'"],
        ["ddl_execution_mode=not-executed", "ddl_execution_mode='not-executed'"],
        ["mode=dry-run"],
        ["runtime guard"],
        ["rollback"],
        ["audit-only"],
        ["sha256"],
    ]

    missing_markers: list[str] = []
    for group in required_marker_groups:
        if not any(marker in combined_text for marker in group):
            missing_markers.append(" OR ".join(group))

    return {
        "step156a_directory": str(STEP156A_DIR),
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


def main() -> None:
    required_paths = [
        DRAFT_SCRIPT_PATH,
        EXECUTION_PREVIEW_EXPORTER_PATH,
        EXECUTION_PREVIEW_CHECKER_PATH,
        EXECUTION_PREVIEW_PATH,
        MIGRATION_SCRIPT_PREVIEW_PATH,
        DDL_PREVIEW_PATH,
        CONFIG_PATH,
        PREDICTION_PATH,
        SCHEMA_SQL_PATH,
        DB_PATH,
        README_PATH,
    ]

    for path in required_paths:
        require_file(path)

    validate_config_disabled()

    for path in PROTECTED_DIFF_PATHS:
        require_not_modified(path)

    execution_preview_validation = validate_execution_preview()
    execution_checker_validation = validate_execution_checker_runtime()
    draft_runtime_validation = validate_draft_runtime()
    ddl_candidates_audit = audit_ddl_candidates()
    step156a_log_inspection = inspect_step156a_logs()

    if ddl_candidates_audit["table_count"] != 8:
        fail("DDL_CANDIDATES table_count must be 8")

    if ddl_candidates_audit["danger_pattern_count"] != 0:
        fail("DDL_CANDIDATES danger_pattern_count must be 0")

    preview = {
        "step": "STEP156-B",
        "preview_type": "phase1-mvp-db-schema-runtime-guard-preview",
        "connection_mode": "runtime-guard-preview-only",
        "safe_mode": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "output": str(OUTPUT_PATH),
        "source_files": {
            "draft_script": str(DRAFT_SCRIPT_PATH),
            "execution_preview_exporter": str(EXECUTION_PREVIEW_EXPORTER_PATH),
            "execution_preview_checker": str(EXECUTION_PREVIEW_CHECKER_PATH),
            "execution_preview_json": str(EXECUTION_PREVIEW_PATH),
            "migration_script_preview": str(MIGRATION_SCRIPT_PREVIEW_PATH),
            "ddl_preview": str(DDL_PREVIEW_PATH),
            "config": str(CONFIG_PATH),
            "prediction_json": str(PREDICTION_PATH),
            "schema_sql": str(SCHEMA_SQL_PATH),
            "sqlite_database": str(DB_PATH),
            "step156a_audit_directory": str(STEP156A_DIR),
        },
        "runtime_guard_preview_only": True,
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
        "runtime_guard_requirements": {
            "explicit_execute_flag_required": True,
            "default_mode_must_remain_dry_run": True,
            "clean_git_status_required": True,
            "protected_file_hash_record_required": True,
            "sqlite_backup_required": True,
            "readiness_checks_required": True,
            "ddl_candidates_audit_required": True,
            "create_table_if_not_exists_only": True,
            "future_candidate_statement": "CREATE TABLE IF NOT EXISTS",
            "destructive_sql_forbidden": True,
            "preserve_history_tables": True,
            "history_tables_to_preserve": ["history_races", "history_results"],
            "prediction_json_write_forbidden": True,
            "config_enablement_forbidden": True,
            "prediction_core_connection_forbidden": True,
            "automatic_betting_forbidden": True,
            "runtime_execution_must_be_separate_explicit_step": True,
        },
        "forbidden_sql_patterns": FORBIDDEN_SQL_PATTERNS,
        "rollback_requirements": {
            "sqlite_backup_required": True,
            "backup_target": str(DB_PATH),
            "record_git_status_before_execution": True,
            "record_commit_hash_before_execution": True,
            "record_protected_file_hashes_before_execution": True,
            "record_sha256_files": [
                str(SCHEMA_SQL_PATH),
                str(DB_PATH),
                str(PREDICTION_PATH),
                str(CONFIG_PATH),
            ],
            "record_sqlite_table_list_before_execution": True,
            "record_row_counts_before_execution": True,
            "restore_sqlite_backup": True,
            "git_restore_tracked_files": True,
            "do_not_drop_history_races": True,
            "do_not_drop_history_results": True,
            "do_not_recreate_existing_history_tables": True,
            "do_not_delete_or_update_existing_history_records": True,
        },
        "protected_file_hashes_for_preview": protected_file_hashes(),
        "draft_alignment": {
            "draft_script": str(DRAFT_SCRIPT_PATH),
            "draft_mode": "dry-run",
            "draft_step": "STEP154-B",
            "draft_runtime_validation": draft_runtime_validation,
            "ddl_candidates_audit": ddl_candidates_audit,
        },
        "execution_preview_validation": execution_preview_validation,
        "execution_checker_validation": execution_checker_validation,
        "step156a_audit_reference": step156a_log_inspection,
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
            "deferred_tables_not_created_in_step156_b": True,
        },
        "pre_night_safety_constraints": {
            "pre_night_only": True,
            "results_and_payouts_allowed_as_pre_night_inputs": False,
            "forbidden_information": PRE_NIGHT_FORBIDDEN_INFORMATION,
        },
        "safety_decisions": {
            "do_not_modify_draft_script_in_step156_b": True,
            "do_not_modify_execution_preview_exporter_in_step156_b": True,
            "do_not_modify_execution_preview_checker_in_step156_b": True,
            "do_not_modify_readiness_scripts_in_step156_b": True,
            "do_not_modify_schema_sql_in_step156_b": True,
            "do_not_modify_sqlite_db_in_step156_b": True,
            "do_not_modify_prediction_json_in_step156_b": True,
            "do_not_enable_history_features_in_step156_b": True,
            "do_not_connect_prediction_core_in_step156_b": True,
            "do_not_execute_migration_in_step156_b": True,
            "do_not_execute_ddl_in_step156_b": True,
        },
        "next_step": {
            "step": "STEP156-C",
            "description": "Create checker for Phase 1 MVP DB schema runtime guard preview JSON.",
            "must_not_execute_migration": True,
            "must_not_execute_ddl": True,
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

    if preview["runtime_guard_preview_only"] is not True:
        fail("runtime_guard_preview_only must be True")

    if preview["minimal_table_count"] != 8:
        fail("minimal_table_count must be 8")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(preview, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print("Phase 1 MVP DB schema runtime guard preview export: OK")
    print("STEP 156-B CHECK: OK")
    print(f"preview_type={preview['preview_type']}")
    print(f"connection_mode={preview['connection_mode']}")
    print(f"runtime_guard_preview_only={preview['runtime_guard_preview_only']}")
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
    print(f"explicit_execute_flag_required={preview['runtime_guard_requirements']['explicit_execute_flag_required']}")
    print(f"default_mode_must_remain_dry_run={preview['runtime_guard_requirements']['default_mode_must_remain_dry_run']}")
    print(f"sqlite_backup_required={preview['runtime_guard_requirements']['sqlite_backup_required']}")
    print(f"ddl_candidates_audit_required={preview['runtime_guard_requirements']['ddl_candidates_audit_required']}")
    print(f"ddl_candidates_table_count={ddl_candidates_audit['table_count']}")
    print(f"ddl_candidates_danger_pattern_count={ddl_candidates_audit['danger_pattern_count']}")


if __name__ == "__main__":
    main()
