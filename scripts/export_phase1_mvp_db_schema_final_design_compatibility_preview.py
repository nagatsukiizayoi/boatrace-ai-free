#!/usr/bin/env python3
from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STEP = "STEP158-B"
PREVIEW_TYPE = "phase1-mvp-db-schema-final-design-compatibility-preview"
CONNECTION_MODE = "final-design-compatibility-preview-only"

OUTPUT_JSON = Path("docs/phase1_mvp_db_schema_final_design_compatibility_preview.json")

EXPLICIT_GATE_JSON = Path("docs/phase1_mvp_db_schema_explicit_execution_gate_preview.json")
RUNTIME_GUARD_JSON = Path("docs/phase1_mvp_db_schema_runtime_guard_preview.json")
EXECUTION_PREVIEW_JSON = Path("docs/phase1_mvp_db_schema_migration_execution_preview.json")
MIGRATION_DRAFT_SCRIPT = Path("scripts/migrate_phase1_mvp_db_schema.py")

AUDIT_DIR = Path("/tmp/history_feature_158a")

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

PROTECTED_FILES = [
    Path("scripts/migrate_phase1_mvp_db_schema.py"),
    Path("scripts/export_phase1_mvp_db_schema_explicit_execution_gate_preview.py"),
    Path("scripts/check_phase1_mvp_db_schema_explicit_execution_gate_preview.py"),
    Path("docs/phase1_mvp_db_schema_explicit_execution_gate_preview.json"),
    Path("scripts/export_phase1_mvp_db_schema_runtime_guard_preview.py"),
    Path("scripts/check_phase1_mvp_db_schema_runtime_guard_preview.py"),
    Path("docs/phase1_mvp_db_schema_runtime_guard_preview.json"),
    Path("docs/phase1_mvp_db_schema_migration_execution_preview.json"),
    Path("docs/phase1_mvp_db_schema_migration_script_preview.json"),
    Path("docs/phase1_mvp_db_schema_ddl_preview.json"),
    Path("docs/phase1_mvp_db_schema_implementation_plan_preview.json"),
    Path("docs/phase1_mvp_db_schema_preview.json"),
    Path("db/schema.sql"),
    Path("db/boatrace.sqlite3"),
    Path("docs/prediction.json"),
    Path("data/history_feature_config.json"),
    Path("README.md"),
    Path("requirements.txt"),
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


def ensure_no_diff(path: Path) -> None:
    if not path.exists():
        return
    proc = subprocess.run(
        ["git", "--no-pager", "diff", "--", str(path)],
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        fail(proc.stderr.strip() or f"git diff failed for {path}")
    if proc.stdout.strip():
        fail(f"{path} has uncommitted diff")


def sha256_file(path: Path) -> str:
    require_file(path)
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_explicit_execution_gate_preview() -> None:
    data = load_json(EXPLICIT_GATE_JSON)

    expected = {
        "step": "STEP157-B",
        "preview_type": "phase1-mvp-db-schema-explicit-execution-gate-preview",
        "connection_mode": "explicit-execution-gate-preview-only",
        "safe_mode": True,
        "explicit_execution_gate_preview_only": True,
        "migration_execution_mode": "not-executed",
        "ddl_execution_mode": "not-executed",
        "minimal_table_count": 8,
        "explicit_execute_flag_required": True,
        "default_mode_must_remain_dry_run": True,
        "fail_closed_on_missing_gate": True,
        "runtime_guard_preview_required": True,
        "ddl_candidates_table_count": 8,
        "ddl_candidates_danger_pattern_count": 0,
    }

    for key, value in expected.items():
        require_value(data, key, value)

    for key, value in FALSE_FLAGS.items():
        require_value(data, key, value)

    if find_key(data, "minimal_tables") != PHASE1_MVP_TABLES:
        fail("explicit execution gate minimal_tables mismatch")


def validate_runtime_guard_preview() -> None:
    data = load_json(RUNTIME_GUARD_JSON)

    expected = {
        "step": "STEP156-B",
        "preview_type": "phase1-mvp-db-schema-runtime-guard-preview",
        "connection_mode": "runtime-guard-preview-only",
        "safe_mode": True,
        "runtime_guard_preview_only": True,
        "migration_execution_mode": "not-executed",
        "ddl_execution_mode": "not-executed",
        "minimal_table_count": 8,
    }

    for key, value in expected.items():
        require_value(data, key, value)

    for key, value in FALSE_FLAGS.items():
        require_value(data, key, value)


def validate_execution_preview() -> None:
    data = load_json(EXECUTION_PREVIEW_JSON)

    expected = {
        "step": "STEP155-B",
        "preview_type": "phase1-mvp-db-schema-migration-execution-preview",
        "connection_mode": "execution-preview-only",
        "safe_mode": True,
        "execution_preview_only": True,
        "migration_execution_mode": "not-executed",
        "ddl_execution_mode": "not-executed",
        "minimal_table_count": 8,
    }

    for key, value in expected.items():
        require_value(data, key, value)

    for key, value in FALSE_FLAGS.items():
        require_value(data, key, value)


def audit_ddl_candidates() -> dict[str, Any]:
    require_file(MIGRATION_DRAFT_SCRIPT)
    tree = ast.parse(MIGRATION_DRAFT_SCRIPT.read_text(encoding="utf-8"))

    ddl_candidates = None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "DDL_CANDIDATES":
                    ddl_candidates = ast.literal_eval(node.value)

    if not isinstance(ddl_candidates, dict):
        fail("DDL_CANDIDATES not found or not dict")

    tables = list(ddl_candidates.keys())
    if tables != PHASE1_MVP_TABLES:
        fail(f"DDL_CANDIDATES table mismatch: {tables!r}")

    danger_hits = []
    table_audits = []

    for table_name, ddl in ddl_candidates.items():
        if not isinstance(ddl, str):
            fail(f"DDL for {table_name} is not string")

        ddl_upper = ddl.upper()
        has_create = "CREATE TABLE IF NOT EXISTS" in ddl_upper
        hits = [pattern for pattern in FORBIDDEN_SQL_PATTERNS if pattern in ddl_upper]

        if not has_create:
            fail(f"{table_name} missing CREATE TABLE IF NOT EXISTS")
        if hits:
            danger_hits.append({"table": table_name, "hits": hits})

        table_audits.append({
            "table": table_name,
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


def validate_158a_audit_dir() -> dict[str, Any]:
    required_files = [
        AUDIT_DIR / "explicit_execution_gate_preview_audit.txt",
        AUDIT_DIR / "final_design_table_mapping.txt",
        AUDIT_DIR / "phase1_mvp_scope_audit.txt",
        AUDIT_DIR / "deferred_tables_policy.txt",
        AUDIT_DIR / "pre_night_constraints_audit.txt",
        AUDIT_DIR / "pdf_operation_constraints_audit.txt",
        AUDIT_DIR / "future_migration_execution_readiness_notes.txt",
        AUDIT_DIR / "protected_file_hashes.txt",
        AUDIT_DIR / "step158a_summary.txt",
    ]

    for path in required_files:
        require_file(path)

    combined = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in required_files
    )

    required_markers = [
        "explicit execution gate preview audit: OK",
        "Phase 1 MVP is a safe subset of the final design",
        "minimal_table_count=8",
        "PRE_NIGHT",
        "same-day odds",
        "results_and_payouts_allowed_as_pre_night_inputs=False",
        "no automatic betting",
        "5 to 15 minutes",
        "nightly SQLite merge",
        "LLM not used for normal prediction",
        "sha256=",
        "audit-only",
    ]

    missing = [marker for marker in required_markers if marker not in combined]
    if missing:
        fail(f"STEP158-A audit marker missing: {missing!r}")

    return {
        "audit_dir": str(AUDIT_DIR),
        "required_files": [str(path) for path in required_files],
        "required_markers": required_markers,
    }


def build_preview() -> dict[str, Any]:
    for path in [
        EXPLICIT_GATE_JSON,
        RUNTIME_GUARD_JSON,
        EXECUTION_PREVIEW_JSON,
        MIGRATION_DRAFT_SCRIPT,
        Path("db/schema.sql"),
        Path("db/boatrace.sqlite3"),
        Path("docs/prediction.json"),
        Path("data/history_feature_config.json"),
    ]:
        require_file(path)

    for path in PROTECTED_FILES:
        ensure_no_diff(path)

    validate_explicit_execution_gate_preview()
    validate_runtime_guard_preview()
    validate_execution_preview()

    ddl_audit = audit_ddl_candidates()
    audit_158a = validate_158a_audit_dir()

    protected_hashes = {
        "db/schema.sql": sha256_file(Path("db/schema.sql")),
        "db/boatrace.sqlite3": sha256_file(Path("db/boatrace.sqlite3")),
        "docs/prediction.json": sha256_file(Path("docs/prediction.json")),
        "data/history_feature_config.json": sha256_file(Path("data/history_feature_config.json")),
        "docs/phase1_mvp_db_schema_explicit_execution_gate_preview.json": sha256_file(EXPLICIT_GATE_JSON),
        "docs/phase1_mvp_db_schema_runtime_guard_preview.json": sha256_file(RUNTIME_GUARD_JSON),
        "docs/phase1_mvp_db_schema_migration_execution_preview.json": sha256_file(EXECUTION_PREVIEW_JSON),
    }

    preview: dict[str, Any] = {
        "step": STEP,
        "preview_type": PREVIEW_TYPE,
        "connection_mode": CONNECTION_MODE,
        "safe_mode": True,
        "final_design_compatibility_preview_only": True,
        "migration_execution_mode": "not-executed",
        "ddl_execution_mode": "not-executed",
        **FALSE_FLAGS,
        "minimal_table_count": 8,
        "minimal_tables": PHASE1_MVP_TABLES,
        "final_design_table_count": len(FINAL_DESIGN_TABLES),
        "final_design_tables": FINAL_DESIGN_TABLES,
        "deferred_table_count": len(DEFERRED_TABLES),
        "deferred_tables": DEFERRED_TABLES,
        "compatibility_decisions": {
            "phase1_is_safe_subset_of_final_design": True,
            "phase1_mvp_is_pre_night_first": True,
            "live_update_tables_deferred": True,
            "odds_exhibition_weather_tables_deferred": True,
            "model_training_tables_deferred": True,
            "stage_transition_tables_deferred": True,
            "future_phases_required_for_full_design": True,
        },
        "phase1_is_safe_subset_of_final_design": True,
        "phase1_mvp_is_pre_night_first": True,
        "live_update_tables_deferred": True,
        "odds_exhibition_weather_tables_deferred": True,
        "model_training_tables_deferred": True,
        "stage_transition_tables_deferred": True,
        "future_phases_required_for_full_design": True,
        "pre_night_constraints": {
            "pre_night_only": True,
            "same_day_odds_allowed": False,
            "final_odds_allowed": False,
            "exhibition_data_allowed": False,
            "same_day_weather_after_cutoff_allowed": False,
            "confirmed_outcomes_allowed": False,
            "results_and_payouts_allowed_as_pre_night_inputs": False,
        },
        "pre_night_only": True,
        "same_day_odds_allowed": False,
        "final_odds_allowed": False,
        "exhibition_data_allowed": False,
        "same_day_weather_after_cutoff_allowed": False,
        "confirmed_outcomes_allowed": False,
        "results_and_payouts_allowed_as_pre_night_inputs": False,
        "pdf_operation_constraints": {
            "no_automatic_betting": True,
            "collection_interval_policy": "5 to 15 minutes",
            "sqlite_commit_policy": "nightly SQLite merge",
            "llm_usage_policy": "LLM not used for normal prediction",
            "smartphone_centric_operation": True,
            "low_frequency_collection": True,
            "cache_collected_data": True,
            "nightly_sqlite_merge": True,
        },
        "no_automatic_betting": True,
        "collection_interval_policy": "5 to 15 minutes",
        "sqlite_commit_policy": "nightly SQLite merge",
        "llm_usage_policy": "LLM not used for normal prediction",
        "smartphone_centric_operation": True,
        "ddl_candidate_audit": ddl_audit,
        "ddl_candidates_table_count": ddl_audit["ddl_candidates_table_count"],
        "ddl_candidates_danger_pattern_count": ddl_audit["ddl_candidates_danger_pattern_count"],
        "forbidden_sql_patterns": FORBIDDEN_SQL_PATTERNS,
        "references": {
            "explicit_execution_gate_preview_json": str(EXPLICIT_GATE_JSON),
            "explicit_execution_gate_preview_step": "STEP157-B",
            "explicit_execution_gate_checker": "STEP157-C",
            "runtime_guard_preview_json": str(RUNTIME_GUARD_JSON),
            "runtime_guard_preview_step": "STEP156-B",
            "execution_preview_json": str(EXECUTION_PREVIEW_JSON),
            "execution_preview_step": "STEP155-B",
            "migration_draft_script": str(MIGRATION_DRAFT_SCRIPT),
            "migration_draft_step": "STEP154-B",
            "step158a_audit_dir": str(AUDIT_DIR),
        },
        "key_policy": {
            "race_id_policy": "race_id = canonical_race_key",
            "canonical_race_key_policy": 'canonical_race_key = race_date + "_" + venue_id + "_" + race_no',
            "canonical_candidate_key_policy": 'canonical_candidate_key = race_id + "_" + lane',
        },
        "protected_file_hashes": protected_hashes,
        "step158a_audit_reference": audit_158a,
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

    return preview


def main() -> None:
    preview = build_preview()

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(
        json.dumps(preview, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print("Phase 1 MVP DB schema final design compatibility preview export: OK")
    print("STEP 158-B CHECK: OK")
    print(f"preview_type={preview['preview_type']}")
    print(f"connection_mode={preview['connection_mode']}")
    print(f"final_design_compatibility_preview_only={preview['final_design_compatibility_preview_only']}")
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
    print(f"phase1_is_safe_subset_of_final_design={preview['phase1_is_safe_subset_of_final_design']}")
    print(f"deferred_table_count={preview['deferred_table_count']}")
    print(f"pre_night_only={preview['pre_night_only']}")
    print(f"no_automatic_betting={preview['no_automatic_betting']}")


if __name__ == "__main__":
    main()
