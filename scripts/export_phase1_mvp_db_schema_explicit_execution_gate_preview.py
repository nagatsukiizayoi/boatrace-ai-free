#!/usr/bin/env python3
from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

OUT = Path("docs/phase1_mvp_db_schema_explicit_execution_gate_preview.json")

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

FALSE_FLAGS = {
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
}

EXPLICIT_EXECUTION_GATE_REQUIREMENTS = {
    "explicit_execute_flag_required": True,
    "default_mode_must_remain_dry_run": True,
    "clean_git_status_required": True,
    "protected_file_hash_record_required": True,
    "sqlite_backup_required": True,
    "readiness_checks_required": True,
    "ddl_candidates_audit_required": True,
    "runtime_guard_preview_required": True,
    "execution_preview_required": True,
    "migration_draft_required": True,
    "create_table_if_not_exists_only": True,
    "destructive_sql_forbidden": True,
    "preserve_history_tables": True,
    "prediction_json_write_forbidden": True,
    "config_enablement_forbidden": True,
    "prediction_core_connection_forbidden": True,
    "automatic_betting_forbidden": True,
    "execution_must_be_separate_explicit_step": True,
    "fail_closed_on_missing_gate": True,
}

FAIL_CLOSED_POLICY = {
    "fail_closed_on_missing_gate": True,
    "fail_closed_on_dirty_git_status": True,
    "fail_closed_on_missing_backup": True,
    "fail_closed_on_missing_hash_record": True,
    "fail_closed_on_readiness_failure": True,
    "fail_closed_on_ddl_candidate_audit_failure": True,
    "fail_closed_on_destructive_sql": True,
    "fail_closed_on_missing_explicit_execute_flag": True,
    "fail_closed_on_non_dry_run_default": True,
}

ROLLBACK_REQUIREMENTS = {
    "sqlite_backup_required": True,
    "restore_sqlite_backup": True,
    "git_restore_tracked_files": True,
    "record_git_status_before_execution": True,
    "record_commit_hash_before_execution": True,
    "record_schema_sql_hash_before_execution": True,
    "record_boatrace_sqlite_hash_before_execution": True,
    "record_prediction_json_hash_before_execution": True,
    "record_history_feature_config_hash_before_execution": True,
    "record_sqlite_table_list_before_execution": True,
    "record_sqlite_row_counts_before_execution": True,
    "readiness_checks_before_execution": True,
    "do_not_drop_history_races": True,
    "do_not_drop_history_results": True,
}


def fail(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")


def require(path: str) -> Path:
    p = Path(path)
    if not p.exists():
        fail(f"required file not found: {p}")
    return p


def sha256(path: str) -> str:
    p = require(path)
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_diff_is_clean(path: str) -> bool:
    p = Path(path)
    if not p.exists():
        return True
    proc = subprocess.run(
        ["git", "--no-pager", "diff", "--", path],
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        fail(f"git diff failed for {path}: {proc.stderr}")
    return proc.stdout.strip() == ""


def audit_ddl_candidates() -> dict:
    script = require("scripts/migrate_phase1_mvp_db_schema.py")
    tree = ast.parse(script.read_text(encoding="utf-8"))

    ddl_candidates = None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "DDL_CANDIDATES":
                    ddl_candidates = ast.literal_eval(node.value)

    if not isinstance(ddl_candidates, dict):
        fail("DDL_CANDIDATES not found or not dict")

    tables = list(ddl_candidates.keys())
    if tables != MINIMAL_TABLES:
        fail(f"DDL_CANDIDATES table mismatch: {tables!r}")

    danger_hits = []
    table_audits = []

    for table, ddl in ddl_candidates.items():
        ddl_upper = ddl.upper()
        has_create = "CREATE TABLE IF NOT EXISTS" in ddl_upper
        hits = [p for p in FORBIDDEN_SQL_PATTERNS if p in ddl_upper]

        if not has_create:
            fail(f"{table} missing CREATE TABLE IF NOT EXISTS")
        if hits:
            danger_hits.append({"table": table, "hits": hits})

        table_audits.append({
            "table": table,
            "has_create_table_if_not_exists": has_create,
            "danger_hits": hits,
        })

    if danger_hits:
        fail(f"DDL danger patterns found: {danger_hits!r}")

    return {
        "ddl_candidates_table_count": len(tables),
        "ddl_candidates_tables": tables,
        "ddl_candidates_danger_pattern_count": len(danger_hits),
        "table_audits": table_audits,
    }


def main() -> None:
    required_files = [
        "docs/phase1_mvp_db_schema_runtime_guard_preview.json",
        "docs/phase1_mvp_db_schema_migration_execution_preview.json",
        "scripts/migrate_phase1_mvp_db_schema.py",
        "db/schema.sql",
        "db/boatrace.sqlite3",
        "docs/prediction.json",
        "data/history_feature_config.json",
    ]

    for f in required_files:
        require(f)

    prohibited_diff_files = [
        "scripts/migrate_phase1_mvp_db_schema.py",
        "scripts/export_phase1_mvp_db_schema_runtime_guard_preview.py",
        "scripts/check_phase1_mvp_db_schema_runtime_guard_preview.py",
        "docs/phase1_mvp_db_schema_runtime_guard_preview.json",
        "scripts/check_dashboard_readiness_outputs_ready.py",
        "scripts/check_history_database_readiness.py",
        "docs/phase1_mvp_db_schema_migration_execution_preview.json",
        "docs/phase1_mvp_db_schema_migration_script_preview.json",
        "docs/phase1_mvp_db_schema_ddl_preview.json",
        "docs/phase1_mvp_db_schema_implementation_plan_preview.json",
        "docs/phase1_mvp_db_schema_preview.json",
        "db/schema.sql",
        "db/boatrace.sqlite3",
        "docs/prediction.json",
        "data/history_feature_config.json",
        "README.md",
        "requirements.txt",
    ]

    dirty = [f for f in prohibited_diff_files if not git_diff_is_clean(f)]
    if dirty:
        fail("prohibited file(s) have uncommitted diff: " + ", ".join(dirty))

    ddl_audit = audit_ddl_candidates()

    preview = {
        "step": "STEP157-B",
        "preview_type": "phase1-mvp-db-schema-explicit-execution-gate-preview",
        "connection_mode": "explicit-execution-gate-preview-only",
        "safe_mode": True,
        "explicit_execution_gate_preview_only": True,
        "migration_execution_mode": "not-executed",
        "ddl_execution_mode": "not-executed",
        **FALSE_FLAGS,
        "minimal_table_count": 8,
        "minimal_tables": MINIMAL_TABLES,
        "explicit_execute_flag_required": True,
        "default_mode_must_remain_dry_run": True,
        "fail_closed_on_missing_gate": True,
        "runtime_guard_preview_required": True,
        "execution_preview_required": True,
        "migration_draft_required": True,
        "explicit_execution_gate_requirements": EXPLICIT_EXECUTION_GATE_REQUIREMENTS,
        "fail_closed_policy": FAIL_CLOSED_POLICY,
        "rollback_requirements": ROLLBACK_REQUIREMENTS,
        "forbidden_sql_patterns": FORBIDDEN_SQL_PATTERNS,
        "ddl_candidate_audit": ddl_audit,
        "ddl_candidates_table_count": ddl_audit["ddl_candidates_table_count"],
        "ddl_candidates_danger_pattern_count": ddl_audit["ddl_candidates_danger_pattern_count"],
        "references": {
            "runtime_guard_preview_json": "docs/phase1_mvp_db_schema_runtime_guard_preview.json",
            "runtime_guard_preview_step": "STEP156-B",
            "runtime_guard_checker": "STEP156-C",
            "execution_preview_json": "docs/phase1_mvp_db_schema_migration_execution_preview.json",
            "execution_preview_step": "STEP155-B",
            "migration_draft_script": "scripts/migrate_phase1_mvp_db_schema.py",
            "migration_draft_step": "STEP154-B",
            "migration_draft_checker": "STEP154-C",
            "step157a_audit_dir": "/tmp/history_feature_157a",
        },
        "key_policy": {
            "race_id_policy": "race_id = canonical_race_key",
            "canonical_race_key_policy": 'canonical_race_key = race_date + "_" + venue_id + "_" + race_no',
            "canonical_candidate_key_policy": 'canonical_candidate_key = race_id + "_" + lane',
        },
        "pdf_operation_constraints": {
            "no_automatic_betting": True,
            "collection_interval_policy": "5 to 15 minutes",
            "sqlite_commit_policy": "nightly SQLite merge",
            "llm_usage_policy": "LLM not used for normal prediction",
        },
        "pre_night_constraints": {
            "pre_night_only": True,
            "results_and_payouts_allowed_as_pre_night_inputs": False,
            "same_day_odds_allowed": False,
            "final_odds_allowed": False,
            "confirmed_outcomes_allowed": False,
        },
        "protected_file_hashes": {
            "db/schema.sql": sha256("db/schema.sql"),
            "db/boatrace.sqlite3": sha256("db/boatrace.sqlite3"),
            "docs/prediction.json": sha256("docs/prediction.json"),
            "data/history_feature_config.json": sha256("data/history_feature_config.json"),
            "docs/phase1_mvp_db_schema_runtime_guard_preview.json": sha256("docs/phase1_mvp_db_schema_runtime_guard_preview.json"),
            "docs/phase1_mvp_db_schema_migration_execution_preview.json": sha256("docs/phase1_mvp_db_schema_migration_execution_preview.json"),
        },
        "safety_decision": {
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
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(preview, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("Phase 1 MVP DB schema explicit execution gate preview export: OK")
    print("STEP 157-B CHECK: OK")
    print(f"preview_type={preview['preview_type']}")
    print(f"connection_mode={preview['connection_mode']}")
    print(f"explicit_execution_gate_preview_only={preview['explicit_execution_gate_preview_only']}")
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
    print(f"explicit_execute_flag_required={preview['explicit_execute_flag_required']}")
    print(f"default_mode_must_remain_dry_run={preview['default_mode_must_remain_dry_run']}")
    print(f"fail_closed_on_missing_gate={preview['fail_closed_on_missing_gate']}")
    print(f"runtime_guard_preview_required={preview['runtime_guard_preview_required']}")
    print(f"ddl_candidates_table_count={preview['ddl_candidates_table_count']}")
    print(f"ddl_candidates_danger_pattern_count={preview['ddl_candidates_danger_pattern_count']}")


if __name__ == "__main__":
    main()
