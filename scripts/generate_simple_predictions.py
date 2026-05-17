#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


DEFAULT_DB_PATH = Path("db/boatrace.sqlite3")
DEFAULT_TARGET_DATE = "2026-05-16"

RUN_KEY_PREFIX = "csv-simple-rule"
MODEL_NAME = "simple_rule_model"
MODEL_VERSION = "0.1.0"

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


def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    return column in table_info(conn, table)


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any]:
    if row is None:
        return {}
    return {key: row[key] for key in row.keys()}


def get_first_number(data: dict[str, Any], keys: list[str], default: float = 0.0) -> float:
    for key in keys:
        value = data.get(key)
        if value is None or value == "":
            continue
        try:
            return float(value)
        except ValueError:
            continue
    return default


def get_first_text(data: dict[str, Any], keys: list[str], default: str = "") -> str:
    for key in keys:
        value = data.get(key)
        if value is None or value == "":
            continue
        return str(value)
    return default


def fallback_value_for_column(column: str, column_type: str) -> Any:
    name = column.lower()
    typ = (column_type or "").upper()

    if name.endswith("_at") or name in {"created_at", "updated_at", "executed_at"}:
        return now_iso()

    if "json" in name or name in {"details", "summary", "features", "scores"}:
        return "{}"

    if name in {"status", "result_status"}:
        return "completed"

    if name in {"level"}:
        return "info"

    if name in {"alert_type"}:
        return "data_quality"

    if "amount" in name or "payout" in name or "profit" in name:
        return 0

    if "count" in name or name.endswith("_no") or name.endswith("_id") or name == "rank":
        return 0

    if (
        "rate" in name
        or "odds" in name
        or "probability" in name
        or "confidence" in name
        or "expected_value" in name
        or "score" in name
    ):
        return 0.0

    if "INT" in typ:
        return 0

    if "REAL" in typ or "FLOA" in typ or "DOUB" in typ:
        return 0.0

    return ""


def insert_dynamic(conn: sqlite3.Connection, table: str, values: dict[str, Any]) -> int:
    """
    テーブル定義を見ながら、存在する列だけにINSERTします。
    NOT NULL列で値が無いものには最低限の補完値を入れます。
    """
    info = table_info(conn, table)
    if not info:
        raise RuntimeError(f"Table not found or has no columns: {table}")

    insert_columns: list[str] = []
    insert_values: list[Any] = []

    for column, meta in info.items():
        # idの自動採番はDBに任せる
        if column == "id" and meta["pk"]:
            continue

        if column in values:
            insert_columns.append(column)
            insert_values.append(values[column])
            continue

        # defaultがある列は省略
        if meta["dflt_value"] is not None:
            continue

        # NOT NULL列は補完
        if meta["notnull"]:
            insert_columns.append(column)
            insert_values.append(fallback_value_for_column(column, meta["type"]))

    placeholders = ", ".join(["?"] * len(insert_columns))
    columns_sql = ", ".join(insert_columns)

    sql = f"""
        INSERT INTO {table} (
            {columns_sql}
        )
        VALUES (
            {placeholders}
        )
    """

    cur = conn.execute(sql, insert_values)
    return int(cur.lastrowid)


def update_dynamic(
    conn: sqlite3.Connection,
    table: str,
    row_id: int,
    values: dict[str, Any],
) -> None:
    info = table_info(conn, table)
    assignments: list[str] = []
    params: list[Any] = []

    for column, value in values.items():
        if column not in info:
            continue
        assignments.append(f"{column} = ?")
        params.append(value)

    if not assignments:
        return

    params.append(row_id)
    conn.execute(
        f"""
        UPDATE {table}
        SET {", ".join(assignments)}
        WHERE id = ?
        """,
        params,
    )


def find_existing_run_id(conn: sqlite3.Connection, run_key: str) -> int | None:
    if not table_exists(conn, "prediction_runs"):
        raise RuntimeError("prediction_runs table not found")

    if not column_exists(conn, "prediction_runs", "run_key"):
        return None

    row = conn.execute(
        "SELECT id FROM prediction_runs WHERE run_key = ?",
        (run_key,),
    ).fetchone()

    if row is None:
        return None

    return int(row["id"])


def delete_existing_run_data(conn: sqlite3.Connection, run_id: int) -> None:
    """
    同じrun_keyを再実行できるように、関連データを削除します。
    テーブルや列が存在する場合だけ削除します。
    """
    prediction_ids: list[int] = []

    if table_exists(conn, "predictions") and column_exists(conn, "predictions", "prediction_run_id"):
        rows = conn.execute(
            "SELECT id FROM predictions WHERE prediction_run_id = ?",
            (run_id,),
        ).fetchall()
        prediction_ids = [int(row["id"]) for row in rows]

    if prediction_ids and table_exists(conn, "prediction_tickets"):
        placeholders = ", ".join(["?"] * len(prediction_ids))
        if column_exists(conn, "prediction_tickets", "prediction_id"):
            conn.execute(
                f"DELETE FROM prediction_tickets WHERE prediction_id IN ({placeholders})",
                prediction_ids,
            )

    if table_exists(conn, "alert_events") and column_exists(conn, "alert_events", "prediction_run_id"):
        conn.execute(
            "DELETE FROM alert_events WHERE prediction_run_id = ?",
            (run_id,),
        )

    if table_exists(conn, "export_logs") and column_exists(conn, "export_logs", "prediction_run_id"):
        conn.execute(
            "DELETE FROM export_logs WHERE prediction_run_id = ?",
            (run_id,),
        )

    if table_exists(conn, "predictions") and column_exists(conn, "predictions", "prediction_run_id"):
        conn.execute(
            "DELETE FROM predictions WHERE prediction_run_id = ?",
            (run_id,),
        )

    conn.execute(
        "DELETE FROM prediction_runs WHERE id = ?",
        (run_id,),
    )


def fetch_races(conn: sqlite3.Connection, target_date: str | None) -> list[sqlite3.Row]:
    where = ""
    params: list[Any] = []

    if target_date:
        where = "WHERE r.race_date = ?"
        params.append(target_date)

    rows = conn.execute(
        f"""
        SELECT
            r.id AS race_id,
            r.*,
            v.venue_code AS venue_code,
            v.venue_name AS venue_name
        FROM races r
        JOIN venues v ON v.id = r.venue_id
        {where}
        ORDER BY r.race_date, v.venue_code, r.race_no
        """,
        params,
    ).fetchall()

    return rows


def fetch_entries(conn: sqlite3.Connection, race_id: int) -> list[dict[str, Any]]:
    entry_rows = conn.execute(
        """
        SELECT *
        FROM race_entries
        WHERE race_id = ?
        ORDER BY frame_no
        """,
        (race_id,),
    ).fetchall()

    entries: list[dict[str, Any]] = []

    for entry_row in entry_rows:
        entry = row_to_dict(entry_row)

        racer = {}
        racer_id = entry.get("racer_id")
        if racer_id is not None and table_exists(conn, "racers"):
            racer_row = conn.execute(
                "SELECT * FROM racers WHERE id = ?",
                (racer_id,),
            ).fetchone()
            racer = row_to_dict(racer_row)

        merged = {}
        merged.update(racer)
        merged.update(entry)

        frame_no = int(merged.get("frame_no") or merged.get("boat_no") or 0)
        boat_no = int(merged.get("boat_no") or merged.get("boat_number") or frame_no)

        national_win_rate = get_first_number(
            merged,
            ["national_win_rate", "win_rate", "racer_win_rate"],
            0.0,
        )
        local_win_rate = get_first_number(
            merged,
            ["local_win_rate", "local_rate"],
            0.0,
        )
        st_timing = get_first_number(
            merged,
            ["st_timing", "avg_st", "start_timing"],
            0.18,
        )

        racer_name = get_first_text(
            merged,
            ["racer_name", "name"],
            f"Racer{boat_no}",
        )

        racer_class = get_first_text(
            merged,
            ["racer_class", "class"],
            "",
        )

        # 簡易スコア
        # 勝率を中心に、当地勝率、ST、枠番有利を少し加味します。
        frame_bonus = {
            1: 0.35,
            2: 0.20,
            3: 0.10,
            4: 0.02,
            5: -0.05,
            6: -0.10,
        }.get(frame_no, 0.0)

        st_bonus = max(0.0, 0.25 - abs(st_timing - 0.15))

        score = (
            national_win_rate * 0.65
            + local_win_rate * 0.35
            + frame_bonus
            + st_bonus
        )

        entries.append(
            {
                "entry_id": int(entry["id"]),
                "racer_id": int(racer_id) if racer_id is not None else None,
                "frame_no": frame_no,
                "boat_no": boat_no,
                "racer_name": racer_name,
                "racer_class": racer_class,
                "national_win_rate": national_win_rate,
                "local_win_rate": local_win_rate,
                "st_timing": st_timing,
                "score": round(score, 4),
            }
        )

    return entries


def create_prediction_run(conn: sqlite3.Connection, run_key: str, target_date: str) -> int:
    existing_id = find_existing_run_id(conn, run_key)
    if existing_id is not None:
        delete_existing_run_data(conn, existing_id)

    values = {
        "run_key": run_key,
        "target_date": target_date,
        "executed_at": now_iso(),
        "model_name": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "status": "completed",
        "message": "Generated from CSV imported race entries by simple rule model",
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }

    run_id = insert_dynamic(conn, "prediction_runs", values)
    return run_id


def create_prediction_for_race(
    conn: sqlite3.Connection,
    run_id: int,
    race: sqlite3.Row,
    entries: list[dict[str, Any]],
) -> int | None:
    if len(entries) < 3:
        create_alert(
            conn,
            run_id,
            int(race["race_id"]),
            level="warning",
            alert_type="data_quality",
            message=f'{race["race_no"]}R は出走表が3艇未満のため予想を作成できません',
        )
        return None

    sorted_entries = sorted(entries, key=lambda x: x["score"], reverse=True)
    top1, top2, top3 = sorted_entries[:3]

    score_gap = top1["score"] - top2["score"]
    confidence = min(0.90, max(0.50, 0.58 + score_gap * 0.03))
    confidence = round(confidence, 3)

    total_amount = 900
    expected_value = round(1.0 + max(0.0, score_gap) * 0.04, 3)

    scores_json = json.dumps(sorted_entries, ensure_ascii=False)
    summary_text = (
        f'{top1["boat_no"]}号艇 {top1["racer_name"]} を本命、'
        f'{top2["boat_no"]}号艇を対抗、'
        f'{top3["boat_no"]}号艇を三番手評価。'
    )

    values = {
        "prediction_run_id": run_id,
        "race_id": int(race["race_id"]),
        "favorite_boat_no": int(top1["boat_no"]),
        "rival_boat_no": int(top2["boat_no"]),
        "darkhorse_boat_no": int(top3["boat_no"]),
        "confidence": confidence,
        "expected_value": expected_value,
        "recommended_total_amount": total_amount,
        "summary": summary_text,
        "prediction_summary": summary_text,
        "features_json": scores_json,
        "scores_json": scores_json,
        "details_json": scores_json,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }

    prediction_id = insert_dynamic(conn, "predictions", values)

    create_tickets(
        conn,
        prediction_id,
        top1,
        top2,
        top3,
        confidence,
    )

    if confidence < 0.60:
        create_alert(
            conn,
            run_id,
            int(race["race_id"]),
            level="warning",
            alert_type="low_confidence",
            message=f'{race["race_no"]}R は上位スコア差が小さく、信頼度が低めです',
        )

    return prediction_id


def create_tickets(
    conn: sqlite3.Connection,
    prediction_id: int,
    top1: dict[str, Any],
    top2: dict[str, Any],
    top3: dict[str, Any],
    confidence: float,
) -> None:
    b1 = int(top1["boat_no"])
    b2 = int(top2["boat_no"])
    b3 = int(top3["boat_no"])

    tickets = [
        {
            "rank": 1,
            "bet_type": "3rentan",
            "combination": f"{b1}-{b2}-{b3}",
            "amount": 400,
            "probability": round(confidence * 0.34, 3),
            "odds": 8.5,
            "expected_value": 1.12,
            "reason": "本命から対抗・三番手への基本形",
        },
        {
            "rank": 2,
            "bet_type": "3rentan",
            "combination": f"{b1}-{b3}-{b2}",
            "amount": 300,
            "probability": round(confidence * 0.28, 3),
            "odds": 11.0,
            "expected_value": 1.04,
            "reason": "三番手の逆転を押さえる形",
        },
        {
            "rank": 3,
            "bet_type": "3renfuku",
            "combination": f"{b1}-{b2}-{b3}",
            "amount": 200,
            "probability": round(confidence * 0.45, 3),
            "odds": 3.2,
            "expected_value": 0.98,
            "reason": "上位3艇の組み合わせ押さえ",
        },
    ]

    for ticket in tickets:
        values = {
            "prediction_id": prediction_id,
            "bet_type": ticket["bet_type"],
            "combination": ticket["combination"],
            "amount": ticket["amount"],
            "probability": ticket["probability"],
            "odds": ticket["odds"],
            "expected_value": ticket["expected_value"],
            "rank": ticket["rank"],
            "confidence": confidence,
            "reason": ticket["reason"],
            "memo": ticket["reason"],
            "is_hit": 0,
            "payout": 0,
            "profit": -int(ticket["amount"]),
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }
        insert_dynamic(conn, "prediction_tickets", values)


def create_alert(
    conn: sqlite3.Connection,
    run_id: int,
    race_id: int,
    level: str,
    alert_type: str,
    message: str,
) -> None:
    if not table_exists(conn, "alert_events"):
        return

    values = {
        "prediction_run_id": run_id,
        "race_id": race_id,
        "level": level,
        "alert_type": alert_type,
        "message": message,
        "details_json": json.dumps({"source": "generate_simple_predictions"}, ensure_ascii=False),
        "details": json.dumps({"source": "generate_simple_predictions"}, ensure_ascii=False),
        "occurred_at": now_iso(),
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }

    insert_dynamic(conn, "alert_events", values)


def print_summary(conn: sqlite3.Connection, run_id: int) -> None:
    race_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM predictions
        WHERE prediction_run_id = ?
        """,
        (run_id,),
    ).fetchone()[0]

    ticket_count = 0
    if table_exists(conn, "prediction_tickets"):
        ticket_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM prediction_tickets t
            JOIN predictions p ON p.id = t.prediction_id
            WHERE p.prediction_run_id = ?
            """,
            (run_id,),
        ).fetchone()[0]

    alert_count = 0
    if table_exists(conn, "alert_events"):
        alert_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM alert_events
            WHERE prediction_run_id = ?
            """,
            (run_id,),
        ).fetchone()[0]

    print("\nGenerated prediction summary:")
    print(f"- prediction_run_id: {run_id}")
    print(f"- races predicted: {race_count}")
    print(f"- tickets: {ticket_count}")
    print(f"- alerts: {alert_count}")


def foreign_key_check(conn: sqlite3.Connection) -> None:
    rows = conn.execute("PRAGMA foreign_key_check;").fetchall()
    if rows:
        print("Foreign key check: NG")
        for row in rows:
            print(row)
        raise SystemExit(1)

    print("Foreign key check: OK")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate simple rule-based predictions from imported race entries."
    )
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path")
    parser.add_argument("--target-date", default=DEFAULT_TARGET_DATE, help="Target race date")
    parser.add_argument("--run-key", default=None, help="Prediction run key")
    args = parser.parse_args()

    db_path = Path(args.db)
    target_date = args.target_date
    run_key = args.run_key or f"{RUN_KEY_PREFIX}-{target_date.replace('-', '')}-001"

    print(f"Database: {db_path}")
    print(f"Target date: {target_date}")
    print(f"Run key: {run_key}")

    with connect_db(db_path) as conn:
        required_tables = [
            "races",
            "venues",
            "race_entries",
            "racers",
            "prediction_runs",
            "predictions",
            "prediction_tickets",
        ]

        for table in required_tables:
            if not table_exists(conn, table):
                raise RuntimeError(f"Required table not found: {table}")

        races = fetch_races(conn, target_date)

        if not races:
            raise SystemExit(
                f"No races found for target_date={target_date}. "
                "先に `python scripts/import_race_csv.py` を実行してください。"
            )

        print(f"Found races: {len(races)}")

        run_id = create_prediction_run(conn, run_key, target_date)

        predicted = 0

        for race in races:
            race_id = int(race["race_id"])
            race_no = race["race_no"]
            venue_name = race["venue_name"]

            entries = fetch_entries(conn, race_id)
            print(f"- {venue_name} {race_no}R entries={len(entries)}")

            prediction_id = create_prediction_for_race(conn, run_id, race, entries)
            if prediction_id is not None:
                predicted += 1

        if predicted == 0:
            raise SystemExit("No predictions were generated")

        conn.commit()

        print_summary(conn, run_id)
        foreign_key_check(conn)

    print("\nSTEP 70 CHECK: OK")


if __name__ == "__main__":
    main()
