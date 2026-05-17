#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


DEFAULT_DB_PATH = Path("db/boatrace.sqlite3")
DEFAULT_THRESHOLD = 1.2

JST = timezone(timedelta(hours=9))


def now_iso() -> str:
    return datetime.now(JST).isoformat(timespec="seconds")


def connect_db(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(
            f"Database not found: {db_path}\n"
            "先に `python scripts/init_db.py --reset` を実行してください。"
        )

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        """,
        (table,),
    ).fetchone()
    return row is not None


def table_info(conn: sqlite3.Connection, table: str) -> dict[str, sqlite3.Row]:
    rows = conn.execute(f"PRAGMA table_info({table});").fetchall()
    return {row["name"]: row for row in rows}


def table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return set(table_info(conn, table).keys())


def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    return column in table_columns(conn, table)


def to_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def get_latest_run_id(conn: sqlite3.Connection, run_key: str | None = None) -> int:
    if not table_exists(conn, "prediction_runs"):
        raise RuntimeError("prediction_runs table not found")

    if run_key:
        if not column_exists(conn, "prediction_runs", "run_key"):
            raise RuntimeError("prediction_runs.run_key column not found")

        row = conn.execute(
            """
            SELECT id
            FROM prediction_runs
            WHERE run_key = ?
            """,
            (run_key,),
        ).fetchone()

        if row is None:
            raise RuntimeError(f"prediction_run not found: run_key={run_key}")

        return int(row["id"])

    order_column = "id"
    if column_exists(conn, "prediction_runs", "executed_at"):
        order_column = "executed_at"

    row = conn.execute(
        f"""
        SELECT id
        FROM prediction_runs
        ORDER BY {order_column} DESC, id DESC
        LIMIT 1
        """
    ).fetchone()

    if row is None:
        raise RuntimeError(
            "No prediction_runs found. "
            "先に `python scripts/generate_simple_predictions.py` を実行してください。"
        )

    return int(row["id"])


def fallback_value_for_column(column: str, column_type: str) -> Any:
    name = column.lower()
    typ = (column_type or "").upper()

    if name.endswith("_at") or name in {"created_at", "updated_at", "occurred_at"}:
        return now_iso()

    if name == "level":
        return "info"

    if name == "alert_type":
        return "total_amount"

    if "json" in name or name in {"details", "metadata"}:
        return "{}"

    if "message" in name:
        return ""

    if "INT" in typ:
        return 0

    if "REAL" in typ or "FLOA" in typ or "DOUB" in typ:
        return 0.0

    return ""


def insert_dynamic(conn: sqlite3.Connection, table: str, values: dict[str, Any]) -> int:
    info = table_info(conn, table)

    if not info:
        raise RuntimeError(f"Table not found or has no columns: {table}")

    insert_columns: list[str] = []
    insert_values: list[Any] = []

    for column, meta in info.items():
        if column == "id" and meta["pk"]:
            continue

        if column in values:
            insert_columns.append(column)
            insert_values.append(values[column])
            continue

        if meta["dflt_value"] is not None:
            continue

        if meta["notnull"]:
            insert_columns.append(column)
            insert_values.append(fallback_value_for_column(column, meta["type"]))

    sql = f"""
        INSERT INTO {table} (
            {", ".join(insert_columns)}
        )
        VALUES (
            {", ".join(["?"] * len(insert_columns))}
        )
    """

    cur = conn.execute(sql, insert_values)
    return int(cur.lastrowid)


def delete_existing_expected_value_alerts(conn: sqlite3.Connection, run_id: int) -> None:
    """
    同じrunで再実行したときにアラートが重複しないように削除します。
    schema差分に対応するため、存在する列だけを使います。
    """
    if not table_exists(conn, "alert_events"):
        return

    cols = table_columns(conn, "alert_events")

    if "prediction_run_id" not in cols:
        return

    conditions = []
    params: list[Any] = [run_id]

    if "message" in cols:
        conditions.append("message LIKE ?")
        params.append("%期待値%")

    if "details_json" in cols:
        conditions.append("details_json LIKE ?")
        params.append("%create_expected_value_alerts%")

    if "details" in cols:
        conditions.append("details LIKE ?")
        params.append("%create_expected_value_alerts%")

    if not conditions:
        return

    sql = f"""
        DELETE FROM alert_events
        WHERE prediction_run_id = ?
          AND ({' OR '.join(conditions)})
    """

    deleted = conn.execute(sql, params).rowcount
    print(f"Deleted existing expected value alerts: {deleted}")


def fetch_high_expected_value_tickets(
    conn: sqlite3.Connection,
    run_id: int,
    threshold: float,
) -> list[sqlite3.Row]:
    required_tables = [
        "prediction_runs",
        "predictions",
        "prediction_tickets",
        "races",
        "venues",
    ]

    for table in required_tables:
        if not table_exists(conn, table):
            raise RuntimeError(f"Required table not found: {table}")

    ticket_cols = table_columns(conn, "prediction_tickets")
    prediction_cols = table_columns(conn, "predictions")

    required_ticket_cols = ["prediction_id", "bet_type", "combination"]
    for col in required_ticket_cols:
        if col not in ticket_cols:
            raise RuntimeError(f"Required column not found: prediction_tickets.{col}")

    if "expected_value" not in ticket_cols:
        raise RuntimeError(
            "prediction_tickets.expected_value column not found. "
            "先に `python scripts/patch_step78_ticket_schema.py` を実行してください。"
        )

    select_columns = [
        "t.id AS ticket_id",
        "p.id AS prediction_id",
        "p.race_id AS race_id",
        "p.prediction_run_id AS prediction_run_id",
        "r.race_date AS race_date",
        "v.venue_code AS venue_code",
        "v.venue_name AS venue_name",
        "r.race_no AS race_no",
        "t.bet_type AS bet_type",
        "t.combination AS combination",
        "t.expected_value AS expected_value",
    ]

    if "odds" in ticket_cols:
        select_columns.append("t.odds AS odds")
    else:
        select_columns.append("NULL AS odds")

    if "probability" in ticket_cols:
        select_columns.append("t.probability AS probability")
    elif "confidence" in ticket_cols:
        select_columns.append("t.confidence AS probability")
    elif "confidence" in prediction_cols:
        select_columns.append("p.confidence AS probability")
    else:
        select_columns.append("NULL AS probability")

    if "amount" in ticket_cols:
        select_columns.append("t.amount AS amount")
    else:
        select_columns.append("NULL AS amount")

    if "rank" in ticket_cols:
        select_columns.append("t.rank AS rank")
        order_sql = "r.race_date, v.venue_code, r.race_no, t.rank, t.id"
    else:
        select_columns.append("NULL AS rank")
        order_sql = "r.race_date, v.venue_code, r.race_no, t.id"

    sql = f"""
        SELECT
            {", ".join(select_columns)}
        FROM prediction_tickets t
        JOIN predictions p ON p.id = t.prediction_id
        JOIN races r ON r.id = p.race_id
        JOIN venues v ON v.id = r.venue_id
        WHERE p.prediction_run_id = ?
          AND t.expected_value IS NOT NULL
          AND t.expected_value >= ?
        ORDER BY {order_sql}
    """

    rows = conn.execute(sql, (run_id, threshold)).fetchall()
    return rows


def build_alert_message(row: sqlite3.Row, threshold: float) -> str:
    race_label = f'{row["venue_name"]} {row["race_no"]}R'
    bet_type = row["bet_type"]
    combination = row["combination"]
    ev = to_float(row["expected_value"])
    odds = to_float(row["odds"])
    probability = to_float(row["probability"])

    return (
        f"期待値高め: {race_label} "
        f"{bet_type} {combination} "
        f"EV={ev:.3f} odds={odds:.2f} prob={probability:.3f} "
        f"(threshold={threshold})"
    )


def create_expected_value_alert(conn: sqlite3.Connection, run_id: int, row: sqlite3.Row, threshold: float) -> int | None:
    if not table_exists(conn, "alert_events"):
        raise RuntimeError("alert_events table not found")

    ev = to_float(row["expected_value"])
    odds = to_float(row["odds"])
    probability = to_float(row["probability"])
    amount = row["amount"]

    details = {
        "source": "create_expected_value_alerts",
        "ticket_id": row["ticket_id"],
        "prediction_id": row["prediction_id"],
        "race_id": row["race_id"],
        "race_date": row["race_date"],
        "venue_code": row["venue_code"],
        "venue_name": row["venue_name"],
        "race_no": row["race_no"],
        "bet_type": row["bet_type"],
        "combination": row["combination"],
        "expected_value": ev,
        "odds": odds,
        "probability": probability,
        "amount": amount,
        "threshold": threshold,
        "message": "expected_value がしきい値以上の買い目です。",
    }

    message = build_alert_message(row, threshold)

    base_values = {
        "prediction_run_id": run_id,
        "race_id": int(row["race_id"]),
        "level": "info",
        "message": message,
        "details_json": json.dumps(details, ensure_ascii=False),
        "details": json.dumps(details, ensure_ascii=False),
        "occurred_at": now_iso(),
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }

    # 既存schemaのCHECK制約に合わせるため、複数候補を試します。
    # 本命は expected_value ですが、古いschemaで許可されていない場合に備えます。
    alert_type_candidates = [
        "expected_value",
        "high_expected_value",
        "value_bet",
        "total_amount",
        "data_quality",
        "missing_final_odds",
        "unknown",
    ]

    level_candidates = [
        "info",
        "warning",
    ]

    for level in level_candidates:
        for alert_type in alert_type_candidates:
            values = dict(base_values)
            values["level"] = level
            values["alert_type"] = alert_type

            try:
                return insert_dynamic(conn, "alert_events", values)
            except sqlite3.IntegrityError:
                continue

    print(
        "Warning: failed to insert alert due to CHECK constraints: "
        f'ticket_id={row["ticket_id"]}, {row["bet_type"]} {row["combination"]}'
    )
    return None


def create_alerts(conn: sqlite3.Connection, run_id: int, threshold: float) -> dict[str, int]:
    delete_existing_expected_value_alerts(conn, run_id)

    rows = fetch_high_expected_value_tickets(conn, run_id, threshold)

    print(f"High expected value tickets found: {len(rows)}")

    created = 0
    failed = 0

    for row in rows:
        alert_id = create_expected_value_alert(conn, run_id, row, threshold)

        if alert_id is None:
            failed += 1
            continue

        created += 1
        print(
            "ALERT",
            f'id={alert_id}',
            f'{row["venue_name"]} {row["race_no"]}R',
            row["bet_type"],
            row["combination"],
            f'EV={row["expected_value"]}',
            f'odds={row["odds"]}',
        )

    return {
        "found": len(rows),
        "created": created,
        "failed": failed,
    }


def print_alert_preview(conn: sqlite3.Connection, run_id: int) -> None:
    if not table_exists(conn, "alert_events"):
        return

    cols = table_columns(conn, "alert_events")

    select_columns = []

    if "id" in cols:
        select_columns.append("id")
    else:
        select_columns.append("NULL AS id")

    if "level" in cols:
        select_columns.append("level")
    else:
        select_columns.append("NULL AS level")

    if "alert_type" in cols:
        select_columns.append("alert_type")
    else:
        select_columns.append("NULL AS alert_type")

    if "message" in cols:
        select_columns.append("message")
    else:
        select_columns.append("NULL AS message")

    if "occurred_at" in cols:
        select_columns.append("occurred_at")
    else:
        select_columns.append("NULL AS occurred_at")

    if "prediction_run_id" not in cols:
        return

    rows = conn.execute(
        f"""
        SELECT
            {", ".join(select_columns)}
        FROM alert_events
        WHERE prediction_run_id = ?
        ORDER BY id
        """,
        (run_id,),
    ).fetchall()

    print("\nAlert preview:")
    for row in rows:
        print(
            f'id={row["id"]}',
            f'level={row["level"]}',
            f'type={row["alert_type"]}',
            f'message={row["message"]}',
            f'occurred_at={row["occurred_at"]}',
        )


def foreign_key_check(conn: sqlite3.Connection) -> None:
    rows = conn.execute("PRAGMA foreign_key_check;").fetchall()

    if rows:
        print("Foreign key check: NG")
        for row in rows:
            print(dict(row))
        raise SystemExit(1)

    print("Foreign key check: OK")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create alert_events for high expected value prediction tickets."
    )
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path")
    parser.add_argument("--run-key", default=None, help="Prediction run key")
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help="Expected value threshold. Default: 1.2",
    )
    args = parser.parse_args()

    db_path = Path(args.db)
    threshold = float(args.threshold)

    print(f"Database: {db_path}")
    print(f"Threshold: {threshold}")

    with connect_db(db_path) as conn:
        required_tables = [
            "prediction_runs",
            "predictions",
            "prediction_tickets",
            "alert_events",
        ]

        for table in required_tables:
            if not table_exists(conn, table):
                raise RuntimeError(f"Required table not found: {table}")

        run_id = get_latest_run_id(conn, args.run_key)
        print(f"Prediction run id: {run_id}")

        result = create_alerts(conn, run_id, threshold)

        conn.commit()

        print("\nExpected value alert summary:")
        print(f"- found: {result['found']}")
        print(f"- created: {result['created']}")
        print(f"- failed: {result['failed']}")

        print_alert_preview(conn, run_id)
        foreign_key_check(conn)

    if result["found"] == 0:
        raise SystemExit(
            "No high expected value tickets found. "
            "先に `python scripts/apply_odds_to_predictions.py` を実行してください。"
        )

    if result["created"] == 0:
        raise SystemExit(
            "No expected value alerts were created. "
            "alert_events の CHECK 制約を確認してください。"
        )

    print("\nSTEP 80 CHECK: OK")


if __name__ == "__main__":
    main()
