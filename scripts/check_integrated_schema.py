#!/usr/bin/env python3
import json
import sqlite3
import subprocess
import sys
from pathlib import Path


PYTHON = sys.executable
DB_PATH = Path("db/boatrace.sqlite3")
PREDICTION_JSON_PATH = Path("docs/prediction.json")


REQUIRED_TABLES = [
    "venues",
    "racers",
    "races",
    "race_entries",
    "odds_snapshots",
    "prediction_runs",
    "predictions",
    "prediction_tickets",
    "alert_events",
    "export_logs",
]


REQUIRED_COLUMNS = {
    "races": [
        "id",
        "race_date",
        "venue_id",
        "race_no",
        "distance",
    ],
    "racers": [
        "id",
        "registration_no",
    ],
    "race_entries": [
        "id",
        "race_id",
        "racer_id",
        "frame_no",
    ],
    "odds_snapshots": [
        "id",
        "race_id",
        "bet_type",
        "combination",
        "odds",
    ],
    "prediction_tickets": [
        "id",
        "prediction_id",
        "bet_type",
        "combination",
        "amount",
        "odds",
        "probability",
        "expected_value",
    ],
}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def run(command: list[str]) -> None:
    print("")
    print("=" * 80)
    print("RUN:", " ".join(command))
    print("=" * 80)

    result = subprocess.run(command)
    if result.returncode != 0:
        fail(f"Command failed with exit code {result.returncode}: {' '.join(command)}")


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def validate_schema() -> None:
    if not DB_PATH.exists():
        fail(f"Database not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    missing_tables = [table for table in REQUIRED_TABLES if not table_exists(conn, table)]
    if missing_tables:
        fail(f"Missing tables: {missing_tables}")

    print("Required tables: OK")

    missing_columns = {}

    for table, cols in REQUIRED_COLUMNS.items():
        actual = table_columns(conn, table)
        missing = [col for col in cols if col not in actual]
        if missing:
            missing_columns[table] = missing

    if missing_columns:
        fail(f"Missing columns: {missing_columns}")

    print("Required columns: OK")

    fk = conn.execute("PRAGMA foreign_key_check;").fetchall()
    if fk:
        fail(f"Foreign key check failed: {fk}")

    print("Foreign key check: OK")

    conn.close()


def validate_counts() -> None:
    conn = sqlite3.connect(DB_PATH)

    tables = [
        "venues",
        "racers",
        "races",
        "race_entries",
        "odds_snapshots",
        "prediction_runs",
        "predictions",
        "prediction_tickets",
        "alert_events",
    ]

    print("")
    print("Table counts:")
    counts = {}

    for table in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        counts[table] = count
        print(f"- {table}: {count}")

    expected_min = {
        "venues": 1,
        "racers": 12,
        "races": 2,
        "race_entries": 12,
        "odds_snapshots": 18,
        "prediction_runs": 1,
        "predictions": 2,
        "prediction_tickets": 6,
        "alert_events": 1,
    }

    errors = []

    for table, minimum in expected_min.items():
        actual = counts.get(table, 0)
        if actual < minimum:
            errors.append(f"{table}: expected >= {minimum}, got {actual}")

    if errors:
        for e in errors:
            print("-", e)
        fail("Table count validation failed")

    conn.close()

    print("Table counts: OK")


def validate_prediction_json() -> None:
    if not PREDICTION_JSON_PATH.exists():
        fail("docs/prediction.json does not exist")

    try:
        data = json.loads(PREDICTION_JSON_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        fail(f"Invalid prediction.json: {e}")

    required_top = [
        "updated_at",
        "run_key",
        "model_name",
        "model_version",
        "target_date",
        "summary",
        "races",
        "alerts",
        "recommendation_reasoning",
    ]

    missing = [key for key in required_top if key not in data]
    if missing:
        fail(f"Missing prediction.json top-level keys: {missing}")

    races = data.get("races", [])
    alerts = data.get("alerts", [])

    if not isinstance(races, list) or not races:
        fail("races must be a non-empty list")

    if not isinstance(alerts, list):
        fail("alerts must be a list")

    recommendations = []
    for race in races:
        recommendations.extend(race.get("recommendations", []))

    if not recommendations:
        fail("No recommendations found")

    odds_count = 0
    ev_count = 0
    reason_count = 0

    for rec in recommendations:
        try:
            odds = float(rec.get("odds") or 0)
        except (TypeError, ValueError):
            odds = 0.0

        try:
            ev = float(rec.get("expected_value") or 0)
        except (TypeError, ValueError):
            ev = 0.0

        if odds > 0:
            odds_count += 1

        if ev > 0:
            ev_count += 1

        if isinstance(rec.get("recommendation_reason"), str) and rec["recommendation_reason"].strip():
            reason_count += 1

    print("")
    print("prediction.json summary:")
    print("races:", len(races))
    print("alerts:", len(alerts))
    print("recommendations:", len(recommendations))
    print("odds_count:", odds_count)
    print("ev_count:", ev_count)
    print("reason_count:", reason_count)

    if odds_count < 1:
        fail("No odds-applied recommendations found")

    if ev_count < 1:
        fail("No expected_value recommendations found")

    if reason_count != len(recommendations):
        fail(f"Not all recommendations have recommendation_reason: {reason_count}/{len(recommendations)}")

    print("prediction.json validation: OK")


def main() -> None:
    print("STEP 104 integrated schema check")
    print("This check intentionally does NOT run patch_step68_schema.py or patch_step78_ticket_schema.py")

    run([PYTHON, "scripts/init_db.py", "--reset"])

    validate_schema()

    # ここから下はパッチなしで実行できることを検証する
    run([PYTHON, "scripts/import_race_csv.py"])
    run([PYTHON, "scripts/import_odds_csv.py"])
    run([PYTHON, "scripts/generate_simple_predictions.py"])
    run([PYTHON, "scripts/apply_odds_to_predictions.py"])
    run([PYTHON, "scripts/create_expected_value_alerts.py"])
    run([PYTHON, "scripts/export_prediction_json.py"])
    run([PYTHON, "scripts/enrich_prediction_json.py"])
    run([PYTHON, "scripts/enrich_recommendation_reasons.py"])

    validate_schema()
    validate_counts()
    validate_prediction_json()

    run([PYTHON, "scripts/check_recommendation_reasons.py"])
    run([PYTHON, "scripts/check_dashboard_final_readiness.py"])

    print("")
    print("Integrated schema validation: OK")
    print("STEP 104 CHECK: OK")


if __name__ == "__main__":
    main()
