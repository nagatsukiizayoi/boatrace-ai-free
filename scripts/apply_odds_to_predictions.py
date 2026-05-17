#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


DEFAULT_DB_PATH = Path("db/boatrace.sqlite3")

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


def table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table});").fetchall()
    return {row["name"] for row in rows}


def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    return column in table_columns(conn, table)


def normalize_combination(bet_type: str, combination: str) -> str:
    """
    3renfuku / 2renfuku は順不同なので、数字をソートして比較します。
    3rentan / 2rentan は順番が重要なのでそのまま比較します。
    """
    text = str(combination or "").strip()

    if not text:
        return ""

    if bet_type in {"3renfuku", "2renfuku", "kakuren"}:
        parts = [p.strip() for p in text.replace(",", "-").split("-") if p.strip()]
        try:
            nums = sorted(int(p) for p in parts)
            return "-".join(str(n) for n in nums)
        except ValueError:
            return text

    return text


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


def fetch_tickets(conn: sqlite3.Connection, run_id: int) -> list[sqlite3.Row]:
    """
    prediction_tickets の列構成が環境により少し違っても動くように、
    存在する列だけを使ってチケットを取得します。

    probability 列がない場合は、
    1. prediction_tickets.confidence
    2. predictions.confidence
    3. 固定値 0.20
    の順で代替します。
    """
    required = [
        ("predictions", "prediction_run_id"),
        ("predictions", "race_id"),
        ("prediction_tickets", "prediction_id"),
        ("prediction_tickets", "bet_type"),
        ("prediction_tickets", "combination"),
    ]

    for table, column in required:
        if not column_exists(conn, table, column):
            raise RuntimeError(f"Required column not found: {table}.{column}")

    ticket_cols = table_columns(conn, "prediction_tickets")
    prediction_cols = table_columns(conn, "predictions")

    select_columns = [
        "t.id AS ticket_id",
        "t.prediction_id AS prediction_id",
        "p.race_id AS race_id",
        "p.prediction_run_id AS prediction_run_id",
        "t.bet_type AS bet_type",
        "t.combination AS combination",
    ]

    if "amount" in ticket_cols:
        select_columns.append("t.amount AS amount")
    else:
        select_columns.append("NULL AS amount")

    # probability の代替順
    if "probability" in ticket_cols:
        select_columns.append("t.probability AS probability")
    elif "ticket_probability" in ticket_cols:
        select_columns.append("t.ticket_probability AS probability")
    elif "hit_probability" in ticket_cols:
        select_columns.append("t.hit_probability AS probability")
    elif "confidence" in ticket_cols:
        select_columns.append("t.confidence AS probability")
    elif "confidence" in prediction_cols:
        select_columns.append("p.confidence AS probability")
    else:
        # 最低限の仮値。後続の expected_value 計算が 0 にならないようにする。
        select_columns.append("0.20 AS probability")

    if "odds" in ticket_cols:
        select_columns.append("t.odds AS current_odds")
    else:
        select_columns.append("NULL AS current_odds")

    if "expected_value" in ticket_cols:
        select_columns.append("t.expected_value AS current_expected_value")
    else:
        select_columns.append("NULL AS current_expected_value")

    if "rank" in ticket_cols:
        order_sql = "p.race_id, t.rank, t.id"
    else:
        order_sql = "p.race_id, t.id"

    sql = f"""
        SELECT
            {", ".join(select_columns)}
        FROM prediction_tickets t
        JOIN predictions p ON p.id = t.prediction_id
        WHERE p.prediction_run_id = ?
        ORDER BY {order_sql}
    """

    rows = conn.execute(sql, (run_id,)).fetchall()

    return rows

def fetch_odds_map(conn: sqlite3.Connection) -> dict[tuple[int, str, str], sqlite3.Row]:
    if not table_exists(conn, "odds_snapshots"):
        raise RuntimeError("odds_snapshots table not found")

    required_columns = ["race_id", "bet_type", "combination", "odds"]
    for column in required_columns:
        if not column_exists(conn, "odds_snapshots", column):
            raise RuntimeError(f"Required column not found: odds_snapshots.{column}")

    captured_col = "captured_at" if column_exists(conn, "odds_snapshots", "captured_at") else "id"

    rows = conn.execute(
        f"""
        SELECT *
        FROM odds_snapshots
        WHERE odds IS NOT NULL
          AND odds > 0
        ORDER BY race_id, bet_type, combination, {captured_col} DESC, id DESC
        """
    ).fetchall()

    odds_map: dict[tuple[int, str, str], sqlite3.Row] = {}

    for row in rows:
        race_id = int(row["race_id"])
        bet_type = str(row["bet_type"])
        combination = normalize_combination(bet_type, str(row["combination"]))

        key = (race_id, bet_type, combination)

        # ORDER BYで新しいものが先に来るので、最初の1件を採用
        if key not in odds_map:
            odds_map[key] = row

    return odds_map


def to_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def update_ticket_odds(
    conn: sqlite3.Connection,
    ticket_id: int,
    odds: float,
    expected_value: float,
) -> None:
    cols = table_columns(conn, "prediction_tickets")

    updates: list[str] = []
    params: list[Any] = []

    if "odds" in cols:
        updates.append("odds = ?")
        params.append(odds)

    if "expected_value" in cols:
        updates.append("expected_value = ?")
        params.append(expected_value)

    if "updated_at" in cols:
        updates.append("updated_at = ?")
        params.append(now_iso())

    if not updates:
        return

    params.append(ticket_id)

    conn.execute(
        f"""
        UPDATE prediction_tickets
        SET {", ".join(updates)}
        WHERE id = ?
        """,
        params,
    )


def insert_dynamic(conn: sqlite3.Connection, table: str, values: dict[str, Any]) -> int:
    info = conn.execute(f"PRAGMA table_info({table});").fetchall()
    if not info:
        raise RuntimeError(f"Table not found or has no columns: {table}")

    columns = {row["name"]: row for row in info}

    insert_columns: list[str] = []
    insert_values: list[Any] = []

    for column, meta in columns.items():
        if column == "id" and meta["pk"]:
            continue

        if column in values:
            insert_columns.append(column)
            insert_values.append(values[column])
            continue

        if meta["dflt_value"] is not None:
            continue

        if meta["notnull"]:
            name = column.lower()
            typ = (meta["type"] or "").upper()

            if name.endswith("_at") or name in {"created_at", "updated_at", "occurred_at"}:
                value = now_iso()
            elif name == "level":
                value = "warning"
            elif name == "alert_type":
                value = "data_quality"
            elif "json" in name or name in {"details"}:
                value = "{}"
            elif "INT" in typ:
                value = 0
            elif "REAL" in typ:
                value = 0.0
            else:
                value = ""

            insert_columns.append(column)
            insert_values.append(value)

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


def create_missing_odds_alert(
    conn: sqlite3.Connection,
    run_id: int,
    race_id: int,
    bet_type: str,
    combination: str,
) -> None:
    if not table_exists(conn, "alert_events"):
        return

    details = {
        "source": "apply_odds_to_predictions",
        "bet_type": bet_type,
        "combination": combination,
        "reason": "prediction_tickets に対応する odds_snapshots が見つかりませんでした。",
    }

    base_values = {
        "prediction_run_id": run_id,
        "race_id": race_id,
        "level": "warning",
        "message": f"オッズ未取得: {bet_type} {combination}",
        "details_json": json.dumps(details, ensure_ascii=False),
        "details": json.dumps(details, ensure_ascii=False),
        "occurred_at": now_iso(),
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }

    # schema の CHECK 制約に合わせて候補を順に試します。
    for alert_type in ["missing_final_odds", "data_quality", "unknown"]:
        values = dict(base_values)
        values["alert_type"] = alert_type

        try:
            insert_dynamic(conn, "alert_events", values)
            return
        except sqlite3.IntegrityError:
            continue

    # どうしても入らない場合は、予想本体を止めない
    print(f"Warning: failed to insert missing odds alert for {bet_type} {combination}")


def apply_odds(conn: sqlite3.Connection, run_id: int, create_alerts: bool = True) -> dict[str, int]:
    tickets = fetch_tickets(conn, run_id)
    odds_map = fetch_odds_map(conn)

    matched = 0
    missing = 0

    print(f"Tickets to update: {len(tickets)}")
    print(f"Available odds keys: {len(odds_map)}")

    for ticket in tickets:
        ticket_id = int(ticket["ticket_id"])
        race_id = int(ticket["race_id"])
        bet_type = str(ticket["bet_type"])
        combination = str(ticket["combination"])
        normalized_combination = normalize_combination(bet_type, combination)

        key = (race_id, bet_type, normalized_combination)
        odds_row = odds_map.get(key)

        if odds_row is None:
            missing += 1
            print(f"MISS ticket_id={ticket_id} race_id={race_id} {bet_type} {combination}")

            if create_alerts:
                create_missing_odds_alert(conn, run_id, race_id, bet_type, combination)

            continue

        odds = to_float(odds_row["odds"])
        probability = to_float(ticket["probability"])

        # expected_value は回収期待倍率として扱います。
        # 例: 的中確率 0.25 × オッズ 8.0 = 2.0
        expected_value = round(probability * odds, 4)

        update_ticket_odds(conn, ticket_id, odds, expected_value)

        matched += 1

        print(
            f"MATCH ticket_id={ticket_id} race_id={race_id} "
            f"{bet_type} {combination} odds={odds} probability={probability} EV={expected_value}"
        )

    return {
        "tickets": len(tickets),
        "matched": matched,
        "missing": missing,
    }


def print_ticket_preview(conn: sqlite3.Connection, run_id: int) -> None:
    """
    prediction_tickets の列構成に差があってもプレビュー表示できるようにします。
    probability 列がない場合は confidence などで代用します。
    """
    ticket_cols = table_columns(conn, "prediction_tickets")
    prediction_cols = table_columns(conn, "predictions")

    select_columns = [
        "r.race_date AS race_date",
        "v.venue_code AS venue_code",
        "v.venue_name AS venue_name",
        "r.race_no AS race_no",
        "t.bet_type AS bet_type",
        "t.combination AS combination",
    ]

    if "probability" in ticket_cols:
        select_columns.append("t.probability AS probability")
    elif "ticket_probability" in ticket_cols:
        select_columns.append("t.ticket_probability AS probability")
    elif "hit_probability" in ticket_cols:
        select_columns.append("t.hit_probability AS probability")
    elif "confidence" in ticket_cols:
        select_columns.append("t.confidence AS probability")
    elif "confidence" in prediction_cols:
        select_columns.append("p.confidence AS probability")
    else:
        select_columns.append("0.20 AS probability")

    if "odds" in ticket_cols:
        select_columns.append("t.odds AS odds")
    else:
        select_columns.append("NULL AS odds")

    if "expected_value" in ticket_cols:
        select_columns.append("t.expected_value AS expected_value")
    else:
        select_columns.append("NULL AS expected_value")

    if "amount" in ticket_cols:
        select_columns.append("t.amount AS amount")
    else:
        select_columns.append("NULL AS amount")

    if "rank" in ticket_cols:
        order_sql = "r.race_date, v.venue_code, r.race_no, t.rank, t.id"
    else:
        order_sql = "r.race_date, v.venue_code, r.race_no, t.id"

    sql = f"""
        SELECT
            {", ".join(select_columns)}
        FROM prediction_tickets t
        JOIN predictions p ON p.id = t.prediction_id
        JOIN races r ON r.id = p.race_id
        JOIN venues v ON v.id = r.venue_id
        WHERE p.prediction_run_id = ?
        ORDER BY {order_sql}
    """

    rows = conn.execute(sql, (run_id,)).fetchall()

    print("\nTicket odds preview:")
    for row in rows:
        print(
            row["race_date"],
            row["venue_code"],
            row["venue_name"],
            f'{row["race_no"]}R',
            row["bet_type"],
            row["combination"],
            f'prob={row["probability"]}',
            f'odds={row["odds"]}',
            f'EV={row["expected_value"]}',
            f'amount={row["amount"]}',
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
        description="Apply imported odds_snapshots to prediction_tickets."
    )
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path")
    parser.add_argument("--run-key", default=None, help="Prediction run key")
    parser.add_argument(
        "--no-alerts",
        action="store_true",
        help="Do not create alert_events for missing odds",
    )
    args = parser.parse_args()

    db_path = Path(args.db)

    print(f"Database: {db_path}")

    with connect_db(db_path) as conn:
        required_tables = [
            "prediction_runs",
            "predictions",
            "prediction_tickets",
            "odds_snapshots",
        ]

        for table in required_tables:
            if not table_exists(conn, table):
                raise RuntimeError(f"Required table not found: {table}")

        run_id = get_latest_run_id(conn, args.run_key)
        print(f"Prediction run id: {run_id}")

        result = apply_odds(conn, run_id, create_alerts=not args.no_alerts)

        conn.commit()

        print("\nApply odds summary:")
        print(f"- tickets: {result['tickets']}")
        print(f"- matched: {result['matched']}")
        print(f"- missing: {result['missing']}")

        print_ticket_preview(conn, run_id)
        foreign_key_check(conn)

    if result["tickets"] == 0:
        raise SystemExit("No prediction tickets found")

    if result["matched"] == 0:
        raise SystemExit(
            "No odds matched prediction tickets. "
            "odds.csv の combination と prediction_tickets の combination を確認してください。"
        )

    print("\nSTEP 78 CHECK: OK")


if __name__ == "__main__":
    main()
