#!/usr/bin/env python3
"""
Export docs/prediction.json from SQLite database.

STEP 64 compact version.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / "db" / "boatrace.sqlite3"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "docs" / "prediction.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export prediction.json from SQLite DB.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--run-key", type=str, default=None)
    return parser.parse_args()


def connect(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(
            f"Database file not found: {db_path}\n"
            "Run first:\n"
            "  python scripts/init_db.py --reset\n"
            "  python scripts/seed_sample_data.py"
        )

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def as_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    try:
        return int(round(float(value)))
    except Exception:
        return default


def as_float(value: Any, default: float | None = None) -> float | None:
    if value is None:
        return default
    try:
        return float(value)
    except Exception:
        return default


def format_time(value: str | None) -> str:
    if not value:
        return ""
    text = str(value)
    if "T" in text:
        return text.split("T", 1)[1][:5]
    return text[:5]


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except Exception:
        return str(path)


def get_latest_run(conn: sqlite3.Connection, run_key: str | None) -> sqlite3.Row:
    if run_key:
        row = conn.execute(
            """
            SELECT *
            FROM prediction_runs
            WHERE run_key = ?
            """,
            (run_key,),
        ).fetchone()
    else:
        row = conn.execute(
            """
            SELECT *
            FROM prediction_runs
            WHERE status = 'completed'
            ORDER BY executed_at DESC, id DESC
            LIMIT 1
            """
        ).fetchone()

    if row is None:
        raise RuntimeError("Prediction run not found.")

    return row


def get_summary(conn: sqlite3.Connection, prediction_run_id: int) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT
          race_count,
          ticket_count,
          total_amount,
          total_payout,
          total_profit,
          return_rate_percent,
          hit_rate_percent
        FROM v_prediction_run_summary
        WHERE prediction_run_id = ?
        """,
        (prediction_run_id,),
    ).fetchone()

    if row is None:
        return {
            "race_count": 0,
            "ticket_count": 0,
            "total_amount": 0,
            "total_payout": 0,
            "total_profit": 0,
            "return_rate_percent": None,
            "hit_rate_percent": None,
        }

    return {
        "race_count": as_int(row["race_count"]),
        "ticket_count": as_int(row["ticket_count"]),
        "total_amount": as_int(row["total_amount"]),
        "total_payout": as_int(row["total_payout"]),
        "total_profit": as_int(row["total_profit"]),
        "return_rate_percent": as_float(row["return_rate_percent"]),
        "hit_rate_percent": as_float(row["hit_rate_percent"]),
    }


def get_latest_odds(conn: sqlite3.Connection, race_id: int, bet_type: str, combination: str) -> float | None:
    row = conn.execute(
        """
        SELECT odds
        FROM odds_snapshots
        WHERE race_id = ?
          AND bet_type = ?
          AND combination = ?
        ORDER BY captured_at DESC, id DESC
        LIMIT 1
        """,
        (race_id, bet_type, combination),
    ).fetchone()

    if row is None:
        return None

    return as_float(row["odds"])


def get_entries(conn: sqlite3.Connection, race_id: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
          e.frame_no,
          e.boat_no,
          e.exhibition_time,
          e.exhibition_st,
          e.entry_course,
          e.motor_no,
          e.boat_number,
          r.racer_registration_no,
          r.racer_name,
          r.branch,
          r.class_name
        FROM race_entries e
        JOIN racers r
          ON r.id = e.racer_id
        WHERE e.race_id = ?
        ORDER BY e.frame_no
        """,
        (race_id,),
    ).fetchall()

    return [
        {
            "frame_no": as_int(row["frame_no"]),
            "boat_no": as_int(row["boat_no"]),
            "racer_registration_no": row["racer_registration_no"],
            "racer_name": row["racer_name"],
            "branch": row["branch"],
            "class_name": row["class_name"],
            "motor_no": row["motor_no"],
            "boat_number": row["boat_number"],
            "exhibition_time": as_float(row["exhibition_time"]),
            "exhibition_st": as_float(row["exhibition_st"]),
            "entry_course": as_int(row["entry_course"]) if row["entry_course"] is not None else None,
        }
        for row in rows
    ]


def get_tickets(conn: sqlite3.Connection, prediction_id: int, race_id: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
          bet_type,
          combination,
          amount,
          estimated_probability,
          expected_odds,
          expected_value,
          rank_no,
          confidence,
          reason,
          is_hit,
          payout_amount,
          profit_amount
        FROM prediction_tickets
        WHERE prediction_id = ?
        ORDER BY
          CASE WHEN rank_no IS NULL THEN 999 ELSE rank_no END,
          id
        """,
        (prediction_id,),
    ).fetchall()

    tickets = []

    for row in rows:
        latest_odds = get_latest_odds(
            conn,
            race_id,
            row["bet_type"],
            row["combination"],
        )

        odds = latest_odds
        if odds is None:
            odds = as_float(row["expected_odds"])

        tickets.append(
            {
                "ticket": row["combination"],
                "combination": row["combination"],
                "bet_type": row["bet_type"],
                "amount": as_int(row["amount"]),
                "odds": odds,
                "final_odds": odds,
                "expected_odds": as_float(row["expected_odds"]),
                "estimated_probability": as_float(row["estimated_probability"]),
                "expected_value": as_float(row["expected_value"]),
                "rank": as_int(row["rank_no"]) if row["rank_no"] is not None else None,
                "confidence": as_float(row["confidence"]),
                "memo": row["reason"] or "",
                "reason": row["reason"] or "",
                "is_hit": row["is_hit"],
                "payout_amount": as_int(row["payout_amount"]),
                "profit_amount": as_int(row["profit_amount"]),
            }
        )

    return tickets


def get_races(conn: sqlite3.Connection, prediction_run_id: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
          p.id AS prediction_id,
          p.race_id,
          p.favorite_boat_no,
          p.rival_boat_no,
          p.darkhorse_boat_no,
          p.confidence,
          p.expected_value,
          p.recommended_total_amount,
          p.prediction_summary,
          ra.race_date,
          ra.race_no,
          ra.race_name,
          ra.grade,
          ra.distance_m,
          ra.deadline_at,
          ra.start_at,
          ra.weather,
          ra.wind_direction,
          ra.wind_speed_m,
          ra.wave_height_cm,
          ra.temperature_c,
          ra.water_temperature_c,
          ra.status,
          ra.source_url,
          v.venue_code,
          v.venue_name
        FROM predictions p
        JOIN races ra
          ON ra.id = p.race_id
        JOIN venues v
          ON v.id = ra.venue_id
        WHERE p.prediction_run_id = ?
        ORDER BY ra.race_date, v.venue_code, ra.race_no
        """,
        (prediction_run_id,),
    ).fetchall()

    races = []

    for row in rows:
        prediction_id = as_int(row["prediction_id"])
        race_id = as_int(row["race_id"])
        recommendations = get_tickets(conn, prediction_id, race_id)
        entries = get_entries(conn, race_id)

        total_amount = as_int(row["recommended_total_amount"])
        if total_amount == 0:
            total_amount = sum(as_int(ticket.get("amount")) for ticket in recommendations)

        title = f"{row['venue_name']} {row['race_no']}R {row['race_name'] or ''}".strip()

        races.append(
            {
                "id": race_id,
                "prediction_id": prediction_id,
                "date": row["race_date"],
                "venue_code": row["venue_code"],
                "venue": row["venue_name"],
                "place": row["venue_name"],
                "race_no": as_int(row["race_no"]),
                "race_name": row["race_name"],
                "raceName": row["race_name"],
                "title": title,
                "grade": row["grade"],
                "distance_m": as_int(row["distance_m"], 1800),
                "deadline": format_time(row["deadline_at"]),
                "deadline_at": row["deadline_at"],
                "start_time": format_time(row["start_at"]),
                "start_at": row["start_at"],
                "weather": row["weather"],
                "wind_direction": row["wind_direction"],
                "wind_speed_m": as_float(row["wind_speed_m"]),
                "wave_height_cm": as_float(row["wave_height_cm"]),
                "temperature_c": as_float(row["temperature_c"]),
                "water_temperature_c": as_float(row["water_temperature_c"]),
                "status": row["status"],
                "url": row["source_url"] or "",
                "detail_url": row["source_url"] or "",
                "favorite_boat_no": as_int(row["favorite_boat_no"]) if row["favorite_boat_no"] is not None else None,
                "rival_boat_no": as_int(row["rival_boat_no"]) if row["rival_boat_no"] is not None else None,
                "darkhorse_boat_no": as_int(row["darkhorse_boat_no"]) if row["darkhorse_boat_no"] is not None else None,
                "confidence": as_float(row["confidence"]),
                "expected_value": as_float(row["expected_value"]),
                "total_amount": total_amount,
                "investment": total_amount,
                "prediction_summary": row["prediction_summary"] or "",
                "comment": row["prediction_summary"] or "",
                "entries": entries,
                "racers": entries,
                "recommendations": recommendations,
                "tickets": recommendations,
            }
        )

    return races


def get_alerts(conn: sqlite3.Connection, prediction_run_id: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
          id,
          race_id,
          level,
          alert_type,
          message,
          details_json,
          occurred_at,
          resolved_at
        FROM alert_events
        WHERE prediction_run_id = ?
        ORDER BY id
        """,
        (prediction_run_id,),
    ).fetchall()

    alerts = []

    for row in rows:
        details = None
        if row["details_json"]:
            try:
                details = json.loads(row["details_json"])
            except Exception:
                details = {"raw": row["details_json"]}

        alerts.append(
            {
                "id": as_int(row["id"]),
                "race_id": row["race_id"],
                "level": row["level"],
                "type": row["alert_type"],
                "message": row["message"],
                "details": details,
                "occurred_at": row["occurred_at"],
                "resolved_at": row["resolved_at"],
            }
        )

    return alerts


def build_payload(conn: sqlite3.Connection, run_key: str | None) -> tuple[dict[str, Any], int]:
    run = get_latest_run(conn, run_key)
    prediction_run_id = as_int(run["id"])

    summary = get_summary(conn, prediction_run_id)
    races = get_races(conn, prediction_run_id)
    alerts = get_alerts(conn, prediction_run_id)

    payload = {
        "updated_at": run["executed_at"],
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "run_key": run["run_key"],
        "prediction_run_id": prediction_run_id,
        "target_date": run["target_date"],
        "model_name": run["model_name"],
        "model_version": run["model_version"],
        "status": run["status"],
        "memo": run["memo"],
        "summary": summary,
        "race_count": summary["race_count"],
        "ticket_count": summary["ticket_count"],
        "total_amount": summary["total_amount"],
        "races": races,
        "alerts": alerts,
    }

    return payload, prediction_run_id


def validate_payload(payload: dict[str, Any]) -> None:
    for key in ["updated_at", "run_key", "summary", "races", "alerts"]:
        if key not in payload:
            raise RuntimeError(f"Missing key: {key}")

    if not isinstance(payload["races"], list):
        raise RuntimeError("races must be list")

    if not isinstance(payload["alerts"], list):
        raise RuntimeError("alerts must be list")

    for race in payload["races"]:
        if "recommendations" not in race:
            raise RuntimeError("race recommendations missing")


def write_json(output_path: Path, payload: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def record_export_log(
    conn: sqlite3.Connection,
    prediction_run_id: int,
    output_path: Path,
    status: str,
    message: str,
) -> None:
    conn.execute(
        """
        INSERT INTO export_logs (
          prediction_run_id,
          export_type,
          output_path,
          exported_at,
          status,
          message
        )
        VALUES (?, 'prediction_json', ?, CURRENT_TIMESTAMP, ?, ?)
        """,
        (
            prediction_run_id,
            display_path(output_path),
            status,
            message,
        ),
    )
    conn.commit()


def print_summary(payload: dict[str, Any], output_path: Path) -> None:
    summary = payload["summary"]

    print("\nExport summary:")
    print(f"  output: {display_path(output_path)}")
    print(f"  run_key: {payload['run_key']}")
    print(f"  target_date: {payload['target_date']}")
    print(f"  model_name: {payload['model_name']}")
    print(f"  model_version: {payload['model_version']}")
    print(f"  race_count: {summary['race_count']}")
    print(f"  ticket_count: {summary['ticket_count']}")
    print(f"  total_amount: {summary['total_amount']}")
    print(f"  total_payout: {summary['total_payout']}")
    print(f"  total_profit: {summary['total_profit']}")
    print(f"  return_rate_percent: {summary['return_rate_percent']}")
    print(f"  hit_rate_percent: {summary['hit_rate_percent']}")
    print(f"  alerts: {len(payload['alerts'])}")


def main() -> None:
    args = parse_args()

    db_path = args.db.resolve()
    output_path = args.output.resolve()

    print(f"Database file: {display_path(db_path)}")
    print(f"Output file: {display_path(output_path)}")

    conn = connect(db_path)
    prediction_run_id = None

    try:
        payload, prediction_run_id = build_payload(conn, args.run_key)
        validate_payload(payload)
        write_json(output_path, payload)

        record_export_log(
            conn,
            prediction_run_id,
            output_path,
            "completed",
            "prediction.json exported successfully",
        )

        print_summary(payload, output_path)

    except Exception as e:
        if prediction_run_id is not None:
            try:
                record_export_log(
                    conn,
                    prediction_run_id,
                    output_path,
                    "failed",
                    str(e),
                )
            except Exception:
                pass
        raise

    finally:
        conn.close()

    print("\nSTEP 64 CHECK: OK")


if __name__ == "__main__":
    main()
