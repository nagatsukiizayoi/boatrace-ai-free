#!/usr/bin/env python3
"""
Export docs/prediction.json from SQLite database.

STEP 64

This script:
- reads prediction data from db/boatrace.sqlite3
- selects the latest prediction run by default
- can select a specific run with --run-key
- exports dashboard-compatible JSON to docs/prediction.json
- records export history into export_logs
- prints validation summary

Usage:
    python scripts/export_prediction_json.py

Full test flow:
    python scripts/init_db.py --reset
    python scripts/seed_sample_data.py
    python scripts/export_prediction_json.py

Use another database:
    python scripts/export_prediction_json.py --db db/test_boatrace.sqlite3

Use another output path:
    python scripts/export_prediction_json.py --output docs/prediction.json

Use a specific prediction run:
    python scripts/export_prediction_json.py --run-key sample-run-20260516-001
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
    parser = argparse.ArgumentParser(
        description="Export dashboard prediction JSON from SQLite database."
    )

    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help="Path to SQLite database. Default: db/boatrace.sqlite3",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Output JSON path. Default: docs/prediction.json",
    )

    parser.add_argument(
        "--run-key",
        type=str,
        default=None,
        help="Prediction run key to export. If omitted, latest completed run is used.",
    )

    parser.add_argument(
        "--pretty",
        action="store_true",
        default=True,
        help="Pretty-print JSON output. Enabled by default.",
    )

    return parser.parse_args()


def connect(db_path: Path) -> sqlite3.Connection:
    db_path = db_path.resolve()

    if not db_path.exists():
        raise FileNotFoundError(
            f"Database file not found: {db_path}\n"
            "Run this first:\n"
            "  python scripts/init_db.py --reset\n"
            "  python scripts/seed_sample_data.py"
        )

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def path_for_display(path: Path) -> str:
    path = path.resolve()
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def format_time(value: str | None) -> str:
    dt = parse_datetime(value)
    if dt is None:
        return str(value or "")
    return dt.strftime("%H:%M")


def as_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return default


def as_float(value: Any, default: float | None = None) -> float | None:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def get_prediction_run(
    conn: sqlite3.Connection,
    run_key: str | None,
) -> dict[str, Any]:
    if run_key:
        row = conn.execute(
            """
            SELECT
              id,
              run_key,
              target_date,
              executed_at,
              model_name,
              model_version,
              status,
              memo
            FROM prediction_runs
            WHERE run_key = ?
            """,
            (run_key,),
        ).fetchone()
    else:
        row = conn.execute(
            """
            SELECT
              id,
              run_key,
              target_date,
              executed_at,
              model_name,
              model_version,
              status,
              memo
            FROM prediction_runs
            WHERE status = 'completed'
            ORDER BY executed_at DESC, id DESC
            LIMIT 1
            """
        ).fetchone()

    if row is None:
        if run_key:
            raise RuntimeError(f"Prediction run not found: {run_key}")
        raise RuntimeError("No completed prediction run found.")

    return dict(row)


def get_prediction_summary(
    conn: sqlite3.Connection,
    prediction_run_id: int,
) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT
          prediction_run_id,
          run_key,
          target_date,
          executed_at,
          model_name,
          model_version,
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


def get_prediction_rows(
    conn: sqlite3.Connection,
    prediction_run_id: int,
) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
          p.id AS prediction_id,
          p.prediction_run_id,
          p.race_id,
          p.favorite_boat_no,
          p.rival_boat_no,
          p.darkhorse_boat_no,
          p.confidence,
          p.expected_value,
          p.recommended_total_amount,
          p.prediction_summary,
          r.race_date,
          r.race_no,
          r.race_name,
          r.grade,
          r.distance_m,
          r.deadline_at,
          r.start_at,
          r.weather,
          r.wind_direction,
          r.wind_speed_m,
          r.wave_height_cm,
          r.temperature_c,
          r.water_temperature_c,
          r.status AS race_status,
          r.source_url,
          v.venue_code,
          v.venue_name
        FROM predictions p
        JOIN races r
          ON r.id = p.race_id
        JOIN venues v
          ON v.id = r.venue_id
        WHERE p.prediction_run_id = ?
        ORDER BY r.race_date ASC, v.venue_code ASC, r.race_no ASC
        """,
        (prediction_run_id,),
    ).fetchall()


def get_ticket_rows(
    conn: sqlite3.Connection,
    prediction_id: int,
) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
          id,
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
          CASE WHEN rank_no IS NULL THEN 999 ELSE rank_no END ASC,
          id ASC
        """,
        (prediction_id,),
    ).fetchall()


def get_race_entries(
    conn: sqlite3.Connection,
    race_id: int,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
          e.frame_no,
          e.boat_no,
          e.motor_no,
          e.boat_number,
          e.national_win_rate,
          e.national_2rentai_rate,
          e.national_3rentai_rate,
          e.local_win_rate,
          e.local_2rentai_rate,
          e.local_3rentai_rate,
          e.motor_2rentai_rate,
          e.motor_3rentai_rate,
          e.boat_2rentai_rate,
          e.boat_3rentai_rate,
          e.exhibition_time,
          e.exhibition_st,
          e.tilt,
          e.entry_course,
          e.start_timing,
          e.finish_order,
          rc.racer_registration_no,
          rc.racer_name,
          rc.branch,
          rc.class_name
        FROM race_entries e
        JOIN racers rc
          ON rc.id = e.racer_id
        WHERE e.race_id = ?
        ORDER BY e.frame_no ASC
        """,
        (race_id,),
    ).fetchall()

    entries: list[dict[str, Any]] = []

    for row in rows:
        entries.append(
            {
                "frame_no": as_int(row["frame_no"]),
                "boat_no": as_int(row["boat_no"]),
                "racer_registration_no": row["racer_registration_no"],
                "racer_name": row["racer_name"],
                "branch": row["branch"],
                "class_name": row["class_name"],
                "motor_no": row["motor_no"],
                "boat_number": row["boat_number"],
                "national_win_rate": as_float(row["national_win_rate"]),
                "national_2rentai_rate": as_float(row["national_2rentai_rate"]),
                "national_3rentai_rate": as_float(row["national_3rentai_rate"]),
                "local_win_rate": as_float(row["local_win_rate"]),
                "local_2rentai_rate": as_float(row["local_2rentai_rate"]),
                "local_3rentai_rate": as_float(row["local_3rentai_rate"]),
                "motor_2rentai_rate": as_float(row["motor_2rentai_rate"]),
                "motor_3rentai_rate": as_float(row["motor_3rentai_rate"]),
                "boat_2rentai_rate": as_float(row["boat_2rentai_rate"]),
                "boat_3rentai_rate": as_float(row["boat_3rentai_rate"]),
                "exhibition_time": as_float(row["exhibition_time"]),
                "exhibition_st": as_float(row["exhibition_st"]),
                "tilt": as_float(row["tilt"]),
                "entry_course": as_int(row["entry_course"]) if row["entry_course"] is not None else None,
                "start_timing": as_float(row["start_timing"]),
                "finish_order": as_int(row["finish_order"]) if row["finish_order"] is not None else None,
            }
        )

    return entries


def get_latest_odds_map(
    conn: sqlite3.Connection,
    race_id: int,
) -> dict[tuple[str, str], float]:
    rows = conn.execute(
        """
        SELECT
          o.bet_type,
          o.combination,
          o.odds
        FROM odds_snapshots o
        JOIN (
          SELECT
            bet_type,
            combination,
            MAX(captured_at) AS latest_captured_at
          FROM odds_snapshots
          WHERE race_id = ?
          GROUP BY bet_type, combination
        ) latest
          ON latest.bet_type = o.bet_type
         AND latest.combination = o.combination
         AND latest.latest_captured_at = o.captured_at
        WHERE o.race_id = ?
        """,
        (race_id, race_id),
    ).fetchall()

    odds_map: dict[tuple[str, str], float] = {}

    for row in rows:
        odds_value = as_float(row["odds"])
        if odds_value is not None:
            odds_map[(row["bet_type"], row["combination"])] = odds_value

    return odds_map


def build_recommendations(
    conn: sqlite3.Connection,
    prediction_id: int,
    race_id: int,
) -> list[dict[str, Any]]:
    ticket_rows = get_ticket_rows(conn, prediction_id)
    odds_map = get_latest_odds_map(conn, race_id)

    recommendations: list[dict[str, Any]] = []

    for row in ticket_rows:
        bet_type = row["bet_type"]
        combination = row["combination"]

        expected_odds = as_float(row["expected_odds"])
        latest_odds = odds_map.get((bet_type, combination))
        display_odds = latest_odds if latest_odds is not None else expected_odds

        recommendations.append(
            {
                "ticket": combination,
                "combination": combination,
                "bet_type": bet_type,
                "amount": as_int(row["amount"]),
                "odds": display_odds,
                "final_odds": display_odds,
                "expected_odds": expected_odds,
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

    return recommendations


def build_races(
    conn: sqlite3.Connection,
    prediction_run_id: int,
) -> list[dict[str, Any]]:
    prediction_rows = get_prediction_rows(conn, prediction_run_id)

    races: list[dict[str, Any]] = []

    for row in prediction_rows:
        prediction_id = as_int(row["prediction_id"])
        race_id = as_int(row["race_id"])
        recommendations = build_recommendations(conn, prediction_id, race_id)
        entries = get_race_entries(conn, race_id)

        total_amount = as_int(row["recommended_total_amount"])
        if total_amount == 0:
            total_amount = sum(as_int(item.get("amount")) for item in recommendations)

        race_title = f"{row['venue_name']} {row['race_no']}R {row['race_name'] or ''}".strip()

        races.append(
            {
                "id": race_id,
                "prediction_id": prediction_id,
                "date": row["race_date"],
                "venue_code": row["venue_code"],
                "venue": row["venue_name"],
                "place": row["venue_name"],
                "race_no": as_int(row["race_no"]),
                "raceName": row["race_name"],
                "race_name": row["race_name"],
                "title": race_title,
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
                "status": row["race_status"],
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


def build_alerts(
    conn: sqlite3.Connection,
    prediction_run_id: int,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
          id,
          prediction_run_id,
          race_id,
          level,
          alert_type,
          message,
          details_json,
          occurred_at,
          resolved_at
        FROM alert_events
        WHERE prediction_run_id = ?
        ORDER BY
          CASE level
            WHEN 'danger' THEN 1
            WHEN 'warning' THEN 2
            WHEN 'info' THEN 3
            ELSE 9
          END ASC,
          occurred_at ASC,
          id ASC
        """,
        (prediction_run_id,),
    ).fetchall()

    alerts: list[dict[str, Any]] = []

    for row in rows:
        details: dict[str, Any] | None = None

        if row["details_json"]:
            try:
                details = json.loads(row["details_json"])
            except json.JSONDecodeError:
                details = {"raw": row["details_json"]}

        alerts.append(
            {
                "id": as_int(row["id"]),
                "level": row["level"],
                "type": row["alert_type"],
                "message": row["message"],
                "race_id": row["race_id"],
                "occurred_at": row["occurred_at"],
                "resolved_at": row["resolved_at"],
                "details": details,
            }
        )

    return alerts


def build_export_payload(
    conn: sqlite3.Connection,
    run_key: str | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    prediction_run = get_prediction_run(conn, run_key)
    prediction_run_id = as_int(prediction_run["id"])

    summary = get_prediction_summary(conn, prediction_run_id)
    races = build_races(conn, prediction_run_id)
    alerts = build_alerts(conn, prediction_run_id)

    total_amount = summary.get("total_amount")
    ticket_count = summary.get("ticket_count")
    race_count = summary.get("race_count")

    payload = {
        "updated_at": prediction_run["executed_at"],
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "run_key": prediction_run["run_key"],
        "prediction_run_id": prediction_run_id,
        "target_date": prediction_run["target_date"],
        "model_name": prediction_run["model_name"],
        "model_version": prediction_run["model_version"],
        "status": prediction_run["status"],
        "memo": prediction_run["memo"],
        "summary": summary,
        "race_count": race_count,
        "ticket_count": ticket_count,
        "total_amount": total_amount,
        "races": races,
        "alerts": alerts,
    }

    return payload, prediction_run


def write_json(output_path: Path, payload: dict[str, Any]) -> None:
    output_path = output_path.resolve()
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
            path_for_display(output_path),
            status,
            message,
        ),
    )
    conn.commit()


def validate_payload(payload: dict[str, Any]) -> None:
    required_top_keys = ["updated_at", "races", "alerts", "summary", "run_key"]

    for key in required_top_keys:
        if key not in payload:
            raise RuntimeError(f"Missing required JSON key: {key}")

    if not isinstance(payload["races"], list):
        raise RuntimeError("JSON key 'races' must be a list.")

    if not isinstance(payload["alerts"], list):
        raise RuntimeError("JSON key 'alerts' must be a list.")

    for race in payload["races"]:
        if "recommendations" not in race:
            raise RuntimeError("Each race must have recommendations.")
        if not isinstance(race["recommendations"], list):
            raise RuntimeError("race.recommendations must be a list.")


def print_export_summary(payload: dict[str, Any], output_path: Path) -> None:
    summary = payload.get("summary", {})

    print("\nExport summary:")
    print(f"  output: {path_for_display(output_path)}")
    print(f"  run_key: {payload.get('run_key')}")
    print(f"  target_date: {payload.get('target_date')}")
    print(f"  model_name: {payload.get('model_name')}")
    print(f"  model_version: {payload.get('model_version')}")
    print(f"  race_count: {summary.get('race_count')}")
    print(f"  ticket_count: {summary.get('ticket_count')}")
    print(f"  total_amount: {summary.get('total_amount')}")
    print(f"  total_payout: {summary.get('total_payout')}")
    print(f"  total_profit: {summary.get('total_profit')}")
    print(f"  return_rate_percent: {summary.get('return_rate_percent')}")
    print(f"  hit_rate_percent: {summary.get('hit_rate_percent')}")
    print(f"  alerts: {len(payload.get('alerts', []))}")


def main() -> None:
    args = parse_args()

    db_path = args.db.resolve()
    output_path = args.output.resolve()

    print(f"Database file: {path_for_display(db_path)}")
    print(f"Output file: {path_for_display(output_path)}")

    conn = connect(db_path)

    prediction_run_id: int | None = None

    try:
        payload, prediction_run = build_export_payload(conn, args.run_key)
        prediction_run_id = as_int(prediction_run["id"])

        validate_payload(payload)
        write_json(output_path, payload)

        record_export_log(
            conn=conn,
            prediction_run_id=prediction_run_id,
            output_path=output_path,
            status="completed",
            message="prediction.json exported successfully",
        )

        print_export_summary(payload, output_path)

    except Exception as e:
        if prediction_run_id is not None:
            try:
                record_export_log(
                    conn=conn,
                    prediction_run_id=prediction_run_id,
                    output_path=output_path,
                    status="failed",
                    message=str(e),
                )
            except Exception:
                pass

        raise

    finally:
        conn.close()

    print("\nSTEP 64 CHECK: OK")


if __name__ == "__main__":
    main()

