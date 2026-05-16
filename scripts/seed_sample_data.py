#!/usr/bin/env python3
"""
Seed sample data into SQLite database for boatrace-ai-free.

STEP 63

This script:
- inserts sample venues
- inserts sample races
- inserts sample racers
- inserts sample race entries
- inserts sample odds snapshots
- inserts a sample prediction run
- inserts sample predictions
- inserts sample prediction tickets
- inserts a sample race result
- updates ticket hit / payout fields
- inserts sample alert events
- prints row counts and prediction summary

Usage:
    python scripts/seed_sample_data.py

Reset database first:
    python scripts/init_db.py --reset
    python scripts/seed_sample_data.py

Use another database file:
    python scripts/seed_sample_data.py --db db/test_boatrace.sqlite3

Delete sample data only:
    python scripts/seed_sample_data.py --reset-data
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / "db" / "boatrace.sqlite3"

SAMPLE_DATE = "2026-05-16"
SAMPLE_RUN_KEY = "sample-run-20260516-001"
SAMPLE_MODEL_NAME = "sample_model"
SAMPLE_MODEL_VERSION = "0.1.0"


TABLES_TO_COUNT = [
    "venues",
    "races",
    "racers",
    "race_entries",
    "odds_snapshots",
    "prediction_runs",
    "predictions",
    "prediction_tickets",
    "race_results",
    "alert_events",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed sample data into SQLite database."
    )

    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help="Path to SQLite database. Default: db/boatrace.sqlite3",
    )

    parser.add_argument(
        "--reset-data",
        action="store_true",
        help="Delete sample data and exit.",
    )

    return parser.parse_args()


def connect(db_path: Path) -> sqlite3.Connection:
    db_path = db_path.resolve()

    if not db_path.exists():
        raise FileNotFoundError(
            f"Database file not found: {db_path}\n"
            "Run this first:\n"
            "  python scripts/init_db.py --reset"
        )

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def fetch_one_id(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...]) -> int:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        raise RuntimeError(f"ID not found for query: {sql} / {params}")
    return int(row[0])


def delete_sample_data(conn: sqlite3.Connection) -> None:
    """
    Delete sample data inserted by this script.

    The order is important because foreign keys exist between tables.
    """
    print("\nDeleting existing sample data...")

    sample_race_ids = [
        int(row["id"])
        for row in conn.execute(
            """
            SELECT r.id
            FROM races r
            JOIN venues v
              ON v.id = r.venue_id
            WHERE r.race_date = ?
              AND v.venue_code IN ('01', '02', '03', '04', '05')
            """,
            (SAMPLE_DATE,),
        ).fetchall()
    ]

    sample_run_ids = [
        int(row["id"])
        for row in conn.execute(
            """
            SELECT id
            FROM prediction_runs
            WHERE run_key = ?
            """,
            (SAMPLE_RUN_KEY,),
        ).fetchall()
    ]

    if sample_run_ids:
        placeholders = ",".join("?" for _ in sample_run_ids)
        conn.execute(
            f"""
            DELETE FROM alert_events
            WHERE prediction_run_id IN ({placeholders})
            """,
            tuple(sample_run_ids),
        )

    if sample_race_ids:
        placeholders = ",".join("?" for _ in sample_race_ids)
        conn.execute(
            f"""
            DELETE FROM alert_events
            WHERE race_id IN ({placeholders})
            """,
            tuple(sample_race_ids),
        )

    conn.execute(
        """
        DELETE FROM prediction_runs
        WHERE run_key = ?
        """,
        (SAMPLE_RUN_KEY,),
    )

    if sample_race_ids:
        placeholders = ",".join("?" for _ in sample_race_ids)
        conn.execute(
            f"""
            DELETE FROM race_results
            WHERE race_id IN ({placeholders})
            """,
            tuple(sample_race_ids),
        )
        conn.execute(
            f"""
            DELETE FROM odds_snapshots
            WHERE race_id IN ({placeholders})
            """,
            tuple(sample_race_ids),
        )
        conn.execute(
            f"""
            DELETE FROM race_entries
            WHERE race_id IN ({placeholders})
            """,
            tuple(sample_race_ids),
        )
        conn.execute(
            f"""
            DELETE FROM races
            WHERE id IN ({placeholders})
            """,
            tuple(sample_race_ids),
        )

    conn.execute(
        """
        DELETE FROM racers
        WHERE racer_registration_no BETWEEN '5001' AND '5012'
        """
    )

    conn.commit()
    print("Sample data deleted.")


def upsert_venue(
    conn: sqlite3.Connection,
    venue_code: str,
    venue_name: str,
    venue_name_kana: str,
    region: str,
) -> int:
    conn.execute(
        """
        INSERT INTO venues (
          venue_code,
          venue_name,
          venue_name_kana,
          region
        )
        VALUES (?, ?, ?, ?)
        ON CONFLICT(venue_code) DO UPDATE SET
          venue_name = excluded.venue_name,
          venue_name_kana = excluded.venue_name_kana,
          region = excluded.region,
          updated_at = CURRENT_TIMESTAMP
        """,
        (venue_code, venue_name, venue_name_kana, region),
    )

    return fetch_one_id(
        conn,
        "SELECT id FROM venues WHERE venue_code = ?",
        (venue_code,),
    )


def upsert_race(
    conn: sqlite3.Connection,
    race_date: str,
    venue_id: int,
    race_no: int,
    race_name: str,
    grade: str,
    deadline_at: str,
    start_at: str,
    weather: str,
    wind_direction: str,
    wind_speed_m: float,
    wave_height_cm: float,
    temperature_c: float,
    water_temperature_c: float,
) -> int:
    conn.execute(
        """
        INSERT INTO races (
          race_date,
          venue_id,
          race_no,
          race_name,
          grade,
          distance_m,
          deadline_at,
          start_at,
          weather,
          wind_direction,
          wind_speed_m,
          wave_height_cm,
          temperature_c,
          water_temperature_c,
          is_stabilizer_used,
          is_fixed_entry,
          status,
          source_url
        )
        VALUES (?, ?, ?, ?, ?, 1800, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 'scheduled', ?)
        ON CONFLICT(race_date, venue_id, race_no) DO UPDATE SET
          race_name = excluded.race_name,
          grade = excluded.grade,
          deadline_at = excluded.deadline_at,
          start_at = excluded.start_at,
          weather = excluded.weather,
          wind_direction = excluded.wind_direction,
          wind_speed_m = excluded.wind_speed_m,
          wave_height_cm = excluded.wave_height_cm,
          temperature_c = excluded.temperature_c,
          water_temperature_c = excluded.water_temperature_c,
          status = excluded.status,
          source_url = excluded.source_url,
          updated_at = CURRENT_TIMESTAMP
        """,
        (
            race_date,
            venue_id,
            race_no,
            race_name,
            grade,
            deadline_at,
            start_at,
            weather,
            wind_direction,
            wind_speed_m,
            wave_height_cm,
            temperature_c,
            water_temperature_c,
            f"https://example.com/races/{race_date}/01/{race_no}",
        ),
    )

    return fetch_one_id(
        conn,
        """
        SELECT id
        FROM races
        WHERE race_date = ?
          AND venue_id = ?
          AND race_no = ?
        """,
        (race_date, venue_id, race_no),
    )


def upsert_racer(
    conn: sqlite3.Connection,
    registration_no: str,
    name: str,
    name_kana: str,
    branch: str,
    birth_prefecture: str,
    class_name: str,
    national_win_rate: float,
    national_2rentai_rate: float,
    national_3rentai_rate: float,
    local_win_rate: float,
    local_2rentai_rate: float,
    local_3rentai_rate: float,
) -> int:
    conn.execute(
        """
        INSERT INTO racers (
          racer_registration_no,
          racer_name,
          racer_name_kana,
          branch,
          birth_prefecture,
          class_name,
          national_win_rate,
          national_2rentai_rate,
          national_3rentai_rate,
          local_win_rate,
          local_2rentai_rate,
          local_3rentai_rate
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(racer_registration_no) DO UPDATE SET
          racer_name = excluded.racer_name,
          racer_name_kana = excluded.racer_name_kana,
          branch = excluded.branch,
          birth_prefecture = excluded.birth_prefecture,
          class_name = excluded.class_name,
          national_win_rate = excluded.national_win_rate,
          national_2rentai_rate = excluded.national_2rentai_rate,
          national_3rentai_rate = excluded.national_3rentai_rate,
          local_win_rate = excluded.local_win_rate,
          local_2rentai_rate = excluded.local_2rentai_rate,
          local_3rentai_rate = excluded.local_3rentai_rate,
          updated_at = CURRENT_TIMESTAMP
        """,
        (
            registration_no,
            name,
            name_kana,
            branch,
            birth_prefecture,
            class_name,
            national_win_rate,
            national_2rentai_rate,
            national_3rentai_rate,
            local_win_rate,
            local_2rentai_rate,
            local_3rentai_rate,
        ),
    )

    return fetch_one_id(
        conn,
        "SELECT id FROM racers WHERE racer_registration_no = ?",
        (registration_no,),
    )


def upsert_race_entry(
    conn: sqlite3.Connection,
    race_id: int,
    racer_id: int,
    frame_no: int,
    boat_no: int,
    motor_no: str,
    boat_number: str,
    national_win_rate: float,
    national_2rentai_rate: float,
    national_3rentai_rate: float,
    local_win_rate: float,
    local_2rentai_rate: float,
    local_3rentai_rate: float,
    motor_2rentai_rate: float,
    motor_3rentai_rate: float,
    boat_2rentai_rate: float,
    boat_3rentai_rate: float,
    exhibition_time: float,
    exhibition_st: float,
    tilt: float,
    entry_course: int,
) -> int:
    conn.execute(
        """
        INSERT INTO race_entries (
          race_id,
          racer_id,
          frame_no,
          boat_no,
          motor_no,
          boat_number,
          national_win_rate,
          national_2rentai_rate,
          national_3rentai_rate,
          local_win_rate,
          local_2rentai_rate,
          local_3rentai_rate,
          motor_2rentai_rate,
          motor_3rentai_rate,
          boat_2rentai_rate,
          boat_3rentai_rate,
          exhibition_time,
          exhibition_st,
          tilt,
          entry_course
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(race_id, frame_no) DO UPDATE SET
          racer_id = excluded.racer_id,
          boat_no = excluded.boat_no,
          motor_no = excluded.motor_no,
          boat_number = excluded.boat_number,
          national_win_rate = excluded.national_win_rate,
          national_2rentai_rate = excluded.national_2rentai_rate,
          national_3rentai_rate = excluded.national_3rentai_rate,
          local_win_rate = excluded.local_win_rate,
          local_2rentai_rate = excluded.local_2rentai_rate,
          local_3rentai_rate = excluded.local_3rentai_rate,
          motor_2rentai_rate = excluded.motor_2rentai_rate,
          motor_3rentai_rate = excluded.motor_3rentai_rate,
          boat_2rentai_rate = excluded.boat_2rentai_rate,
          boat_3rentai_rate = excluded.boat_3rentai_rate,
          exhibition_time = excluded.exhibition_time,
          exhibition_st = excluded.exhibition_st,
          tilt = excluded.tilt,
          entry_course = excluded.entry_course,
          updated_at = CURRENT_TIMESTAMP
        """,
        (
            race_id,
            racer_id,
            frame_no,
            boat_no,
            motor_no,
            boat_number,
            national_win_rate,
            national_2rentai_rate,
            national_3rentai_rate,
            local_win_rate,
            local_2rentai_rate,
            local_3rentai_rate,
            motor_2rentai_rate,
            motor_3rentai_rate,
            boat_2rentai_rate,
            boat_3rentai_rate,
            exhibition_time,
            exhibition_st,
            tilt,
            entry_course,
        ),
    )

    return fetch_one_id(
        conn,
        """
        SELECT id
        FROM race_entries
        WHERE race_id = ?
          AND frame_no = ?
        """,
        (race_id, frame_no),
    )


def insert_odds_snapshot(
    conn: sqlite3.Connection,
    race_id: int,
    bet_type: str,
    combination: str,
    odds: float,
    popularity: int,
    captured_at: str,
) -> None:
    conn.execute(
        """
        INSERT INTO odds_snapshots (
          race_id,
          bet_type,
          combination,
          odds,
          popularity,
          captured_at,
          source
        )
        VALUES (?, ?, ?, ?, ?, ?, 'sample')
        """,
        (race_id, bet_type, combination, odds, popularity, captured_at),
    )


def insert_prediction_run(conn: sqlite3.Connection) -> int:
    conn.execute(
        """
        INSERT INTO prediction_runs (
          run_key,
          target_date,
          executed_at,
          model_name,
          model_version,
          model_params_json,
          data_version,
          source_summary_json,
          status,
          memo
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'completed', ?)
        ON CONFLICT(run_key) DO UPDATE SET
          target_date = excluded.target_date,
          executed_at = excluded.executed_at,
          model_name = excluded.model_name,
          model_version = excluded.model_version,
          model_params_json = excluded.model_params_json,
          data_version = excluded.data_version,
          source_summary_json = excluded.source_summary_json,
          status = excluded.status,
          memo = excluded.memo
        """,
        (
            SAMPLE_RUN_KEY,
            SAMPLE_DATE,
            f"{SAMPLE_DATE}T12:00:00+09:00",
            SAMPLE_MODEL_NAME,
            SAMPLE_MODEL_VERSION,
            json_dumps({"strategy": "sample", "min_confidence": 45}),
            "sample-data-v1",
            json_dumps(
                {
                    "races": 2,
                    "venues": ["桐生"],
                    "note": "STEP 63 sample data",
                }
            ),
            "STEP 63 sample prediction run",
        ),
    )

    return fetch_one_id(
        conn,
        "SELECT id FROM prediction_runs WHERE run_key = ?",
        (SAMPLE_RUN_KEY,),
    )


def upsert_prediction(
    conn: sqlite3.Connection,
    prediction_run_id: int,
    race_id: int,
    favorite_boat_no: int,
    rival_boat_no: int,
    darkhorse_boat_no: int,
    confidence: float,
    expected_value: float,
    recommended_total_amount: int,
    prediction_summary: str,
    scores: dict[str, Any],
) -> int:
    conn.execute(
        """
        INSERT INTO predictions (
          prediction_run_id,
          race_id,
          favorite_boat_no,
          rival_boat_no,
          darkhorse_boat_no,
          confidence,
          expected_value,
          recommended_total_amount,
          prediction_summary,
          features_json,
          scores_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(prediction_run_id, race_id) DO UPDATE SET
          favorite_boat_no = excluded.favorite_boat_no,
          rival_boat_no = excluded.rival_boat_no,
          darkhorse_boat_no = excluded.darkhorse_boat_no,
          confidence = excluded.confidence,
          expected_value = excluded.expected_value,
          recommended_total_amount = excluded.recommended_total_amount,
          prediction_summary = excluded.prediction_summary,
          features_json = excluded.features_json,
          scores_json = excluded.scores_json,
          updated_at = CURRENT_TIMESTAMP
        """,
        (
            prediction_run_id,
            race_id,
            favorite_boat_no,
            rival_boat_no,
            darkhorse_boat_no,
            confidence,
            expected_value,
            recommended_total_amount,
            prediction_summary,
            json_dumps(
                {
                    "exhibition": True,
                    "odds": True,
                    "weather": True,
                    "sample": True,
                }
            ),
            json_dumps(scores),
        ),
    )

    return fetch_one_id(
        conn,
        """
        SELECT id
        FROM predictions
        WHERE prediction_run_id = ?
          AND race_id = ?
        """,
        (prediction_run_id, race_id),
    )


def insert_prediction_ticket(
    conn: sqlite3.Connection,
    prediction_id: int,
    bet_type: str,
    combination: str,
    amount: int,
    estimated_probability: float,
    expected_odds: float,
    expected_value: float,
    rank_no: int,
    confidence: float,
    reason: str,
) -> int:
    conn.execute(
        """
        INSERT INTO prediction_tickets (
          prediction_id,
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
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?)
        """,
        (
            prediction_id,
            bet_type,
            combination,
            amount,
            estimated_probability,
            expected_odds,
            expected_value,
            rank_no,
            confidence,
            reason,
            -amount,
        ),
    )

    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])


def insert_race_result(
    conn: sqlite3.Connection,
    race_id: int,
    first_boat_no: int,
    second_boat_no: int,
    third_boat_no: int,
    trifecta_combination: str,
    trifecta_payout: int,
    trifecta_popularity: int,
) -> int:
    payouts = {
        "3rentan": {
            "combination": trifecta_combination,
            "payout": trifecta_payout,
            "popularity": trifecta_popularity,
        }
    }

    conn.execute(
        """
        INSERT INTO race_results (
          race_id,
          result_status,
          first_boat_no,
          second_boat_no,
          third_boat_no,
          winning_trick,
          has_flying,
          has_late,
          cancellation_json,
          payouts_json,
          trifecta_combination,
          trifecta_payout,
          trifecta_popularity,
          exacta_combination,
          exacta_payout,
          quinella_combination,
          quinella_payout,
          finalized_at,
          source_url
        )
        VALUES (
          ?, 'official', ?, ?, ?, '逃げ', 0, 0, ?, ?,
          ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        ON CONFLICT(race_id) DO UPDATE SET
          result_status = excluded.result_status,
          first_boat_no = excluded.first_boat_no,
          second_boat_no = excluded.second_boat_no,
          third_boat_no = excluded.third_boat_no,
          winning_trick = excluded.winning_trick,
          has_flying = excluded.has_flying,
          has_late = excluded.has_late,
          cancellation_json = excluded.cancellation_json,
          payouts_json = excluded.payouts_json,
          trifecta_combination = excluded.trifecta_combination,
          trifecta_payout = excluded.trifecta_payout,
          trifecta_popularity = excluded.trifecta_popularity,
          exacta_combination = excluded.exacta_combination,
          exacta_payout = excluded.exacta_payout,
          quinella_combination = excluded.quinella_combination,
          quinella_payout = excluded.quinella_payout,
          finalized_at = excluded.finalized_at,
          source_url = excluded.source_url,
          updated_at = CURRENT_TIMESTAMP
        """,
        (
            race_id,
            first_boat_no,
            second_boat_no,
            third_boat_no,
            json_dumps([]),
            json_dumps(payouts),
            trifecta_combination,
            trifecta_payout,
            trifecta_popularity,
            "1-2",
            420,
            "1-2",
            280,
            f"{SAMPLE_DATE}T15:05:00+09:00",
            f"https://example.com/results/{race_id}",
        ),
    )

    return fetch_one_id(
        conn,
        "SELECT id FROM race_results WHERE race_id = ?",
        (race_id,),
    )


def update_ticket_results_for_race(
    conn: sqlite3.Connection,
    prediction_id: int,
    winning_combination: str,
    payout_per_100yen: int,
) -> None:
    tickets = conn.execute(
        """
        SELECT id, combination, amount
        FROM prediction_tickets
        WHERE prediction_id = ?
        """,
        (prediction_id,),
    ).fetchall()

    for ticket in tickets:
        ticket_id = int(ticket["id"])
        combination = str(ticket["combination"])
        amount = int(ticket["amount"])

        if combination == winning_combination:
            payout_amount = int(payout_per_100yen * amount / 100)
            profit_amount = payout_amount - amount
            is_hit = 1
        else:
            payout_amount = 0
            profit_amount = -amount
            is_hit = 0

        conn.execute(
            """
            UPDATE prediction_tickets
            SET
              is_hit = ?,
              payout_amount = ?,
              profit_amount = ?,
              updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (is_hit, payout_amount, profit_amount, ticket_id),
        )


def insert_alert_event(
    conn: sqlite3.Connection,
    prediction_run_id: int,
    race_id: int | None,
    level: str,
    alert_type: str,
    message: str,
    details: dict[str, Any],
) -> int:
    conn.execute(
        """
        INSERT INTO alert_events (
          prediction_run_id,
          race_id,
          level,
          alert_type,
          message,
          details_json,
          occurred_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            prediction_run_id,
            race_id,
            level,
            alert_type,
            message,
            json_dumps(details),
            f"{SAMPLE_DATE}T12:01:00+09:00",
        ),
    )

    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])


def seed_sample_data(conn: sqlite3.Connection) -> None:
    print("\nSeeding venues...")
    venue_ids = {
        "01": upsert_venue(conn, "01", "桐生", "きりゅう", "関東"),
        "02": upsert_venue(conn, "02", "戸田", "とだ", "関東"),
        "03": upsert_venue(conn, "03", "江戸川", "えどがわ", "関東"),
        "04": upsert_venue(conn, "04", "平和島", "へいわじま", "関東"),
        "05": upsert_venue(conn, "05", "多摩川", "たまがわ", "関東"),
    }

    kiryu_id = venue_ids["01"]

    print("Seeding races...")
    race1_id = upsert_race(
        conn,
        race_date=SAMPLE_DATE,
        venue_id=kiryu_id,
        race_no=1,
        race_name="予選",
        grade="一般",
        deadline_at=f"{SAMPLE_DATE}T14:45:00+09:00",
        start_at=f"{SAMPLE_DATE}T14:50:00+09:00",
        weather="晴",
        wind_direction="北",
        wind_speed_m=2.0,
        wave_height_cm=3.0,
        temperature_c=22.4,
        water_temperature_c=19.8,
    )

    race2_id = upsert_race(
        conn,
        race_date=SAMPLE_DATE,
        venue_id=kiryu_id,
        race_no=2,
        race_name="予選",
        grade="一般",
        deadline_at=f"{SAMPLE_DATE}T15:15:00+09:00",
        start_at=f"{SAMPLE_DATE}T15:20:00+09:00",
        weather="晴",
        wind_direction="北東",
        wind_speed_m=1.5,
        wave_height_cm=2.0,
        temperature_c=22.8,
        water_temperature_c=20.1,
    )

    print("Seeding racers...")
    racer_samples = [
        ("5001", "山田太郎", "やまだたろう", "東京", "東京", "A1", 6.82, 48.1, 65.4, 7.10, 52.0, 68.0),
        ("5002", "佐藤一郎", "さとういちろう", "群馬", "群馬", "A2", 6.11, 41.2, 58.7, 6.40, 44.8, 61.0),
        ("5003", "鈴木次郎", "すずきじろう", "静岡", "静岡", "B1", 5.42, 32.5, 49.1, 5.70, 35.0, 52.0),
        ("5004", "高橋三郎", "たかはしさぶろう", "埼玉", "埼玉", "B1", 4.98, 28.2, 43.7, 5.05, 30.1, 46.0),
        ("5005", "田中四郎", "たなかしろう", "愛知", "愛知", "A2", 5.88, 38.4, 55.2, 5.60, 36.2, 53.0),
        ("5006", "伊藤五郎", "いとうごろう", "大阪", "大阪", "B1", 4.71, 24.8, 40.0, 4.90, 27.3, 42.8),
        ("5007", "中村六郎", "なかむらろくろう", "福岡", "福岡", "A1", 7.21, 54.3, 71.2, 6.88, 50.4, 67.5),
        ("5008", "小林七郎", "こばやししちろう", "広島", "広島", "A2", 6.03, 40.0, 57.3, 5.95, 39.2, 56.1),
        ("5009", "加藤八郎", "かとうはちろう", "兵庫", "兵庫", "B1", 5.15, 30.5, 47.8, 5.00, 29.9, 46.4),
        ("5010", "吉田九郎", "よしだくろう", "岡山", "岡山", "B1", 4.66, 23.9, 39.5, 4.82, 26.0, 41.2),
        ("5011", "山本十郎", "やまもとじゅうろう", "長崎", "長崎", "A2", 5.79, 37.1, 54.0, 5.65, 36.4, 52.9),
        ("5012", "松本十一", "まつもとじゅういち", "香川", "香川", "B2", 3.98, 18.5, 31.7, 4.10, 19.8, 33.0),
    ]

    racer_ids: dict[str, int] = {}

    for sample in racer_samples:
        registration_no = sample[0]
        racer_ids[registration_no] = upsert_racer(conn, *sample)

    print("Seeding race entries...")
    race1_registrations = ["5001", "5002", "5003", "5004", "5005", "5006"]
    race2_registrations = ["5007", "5008", "5009", "5010", "5011", "5012"]

    for index, registration_no in enumerate(race1_registrations, start=1):
        upsert_race_entry(
            conn,
            race_id=race1_id,
            racer_id=racer_ids[registration_no],
            frame_no=index,
            boat_no=index,
            motor_no=f"M{20 + index}",
            boat_number=f"B{40 + index}",
            national_win_rate=6.0 - index * 0.12,
            national_2rentai_rate=45.0 - index * 1.8,
            national_3rentai_rate=62.0 - index * 1.5,
            local_win_rate=6.2 - index * 0.10,
            local_2rentai_rate=46.0 - index * 1.5,
            local_3rentai_rate=63.0 - index * 1.2,
            motor_2rentai_rate=35.0 + index,
            motor_3rentai_rate=50.0 + index,
            boat_2rentai_rate=32.0 + index,
            boat_3rentai_rate=48.0 + index,
            exhibition_time=6.70 + index * 0.02,
            exhibition_st=0.08 + index * 0.01,
            tilt=-0.5 if index <= 3 else 0.0,
            entry_course=index,
        )

    for index, registration_no in enumerate(race2_registrations, start=1):
        upsert_race_entry(
            conn,
            race_id=race2_id,
            racer_id=racer_ids[registration_no],
            frame_no=index,
            boat_no=index,
            motor_no=f"M{30 + index}",
            boat_number=f"B{50 + index}",
            national_win_rate=6.3 - index * 0.14,
            national_2rentai_rate=47.0 - index * 1.7,
            national_3rentai_rate=64.0 - index * 1.4,
            local_win_rate=6.1 - index * 0.09,
            local_2rentai_rate=45.0 - index * 1.4,
            local_3rentai_rate=61.0 - index * 1.3,
            motor_2rentai_rate=34.0 + index,
            motor_3rentai_rate=49.0 + index,
            boat_2rentai_rate=31.0 + index,
            boat_3rentai_rate=47.0 + index,
            exhibition_time=6.68 + index * 0.025,
            exhibition_st=0.07 + index * 0.012,
            tilt=-0.5 if index <= 2 else 0.0,
            entry_course=index,
        )

    print("Seeding odds snapshots...")
    odds_samples = [
        (race1_id, "3rentan", "1-2-3", 12.4, 1, f"{SAMPLE_DATE}T14:30:00+09:00"),
        (race1_id, "3rentan", "1-3-2", 18.6, 2, f"{SAMPLE_DATE}T14:30:00+09:00"),
        (race1_id, "3rentan", "2-1-3", 24.8, 5, f"{SAMPLE_DATE}T14:30:00+09:00"),
        (race2_id, "3rentan", "1-2-4", 15.2, 1, f"{SAMPLE_DATE}T15:00:00+09:00"),
        (race2_id, "3rentan", "1-4-2", 21.7, 3, f"{SAMPLE_DATE}T15:00:00+09:00"),
        (race2_id, "3rentan", "2-1-4", 28.1, 6, f"{SAMPLE_DATE}T15:00:00+09:00"),
    ]

    for sample in odds_samples:
        insert_odds_snapshot(conn, *sample)

    print("Seeding prediction run...")
    prediction_run_id = insert_prediction_run(conn)

    print("Seeding predictions...")
    prediction1_id = upsert_prediction(
        conn,
        prediction_run_id=prediction_run_id,
        race_id=race1_id,
        favorite_boat_no=1,
        rival_boat_no=2,
        darkhorse_boat_no=3,
        confidence=72.0,
        expected_value=1.18,
        recommended_total_amount=1200,
        prediction_summary="1号艇の逃げを中心に、2号艇と3号艇を相手本線で評価。",
        scores={
            "1": 88,
            "2": 74,
            "3": 69,
            "4": 50,
            "5": 47,
            "6": 41,
        },
    )

    prediction2_id = upsert_prediction(
        conn,
        prediction_run_id=prediction_run_id,
        race_id=race2_id,
        favorite_boat_no=1,
        rival_boat_no=4,
        darkhorse_boat_no=2,
        confidence=58.0,
        expected_value=1.05,
        recommended_total_amount=600,
        prediction_summary="1号艇中心だが、4号艇の展示気配を評価して押さえる。",
        scores={
            "1": 80,
            "2": 62,
            "3": 48,
            "4": 66,
            "5": 44,
            "6": 38,
        },
    )

    print("Seeding prediction tickets...")
    race1_tickets = [
        ("3rentan", "1-2-3", 400, 0.18, 12.4, 1.22, 1, 76.0, "本命逃げ＋相手上位"),
        ("3rentan", "1-3-2", 300, 0.13, 18.6, 1.08, 2, 68.0, "3号艇の差し残りを評価"),
        ("3rentan", "2-1-3", 300, 0.09, 24.8, 0.96, 3, 55.0, "2号艇差し切りの押さえ"),
        ("3rentan", "1-2-4", 200, 0.10, 19.5, 1.02, 4, 52.0, "4号艇の展示気配を軽く評価"),
    ]

    for sample in race1_tickets:
        insert_prediction_ticket(conn, prediction1_id, *sample)

    race2_tickets = [
        ("3rentan", "1-2-4", 300, 0.14, 15.2, 1.06, 1, 61.0, "1号艇中心、2号艇先攻め"),
        ("3rentan", "1-4-2", 300, 0.12, 21.7, 1.11, 2, 59.0, "4号艇の展示タイムを評価"),
    ]

    for sample in race2_tickets:
        insert_prediction_ticket(conn, prediction2_id, *sample)

    print("Seeding race results...")
    insert_race_result(
        conn,
        race_id=race1_id,
        first_boat_no=1,
        second_boat_no=2,
        third_boat_no=3,
        trifecta_combination="1-2-3",
        trifecta_payout=1240,
        trifecta_popularity=1,
    )

    update_ticket_results_for_race(
        conn,
        prediction_id=prediction1_id,
        winning_combination="1-2-3",
        payout_per_100yen=1240,
    )

    print("Seeding alert events...")
    insert_alert_event(
        conn,
        prediction_run_id=prediction_run_id,
        race_id=None,
        level="warning",
        alert_type="total_amount",
        message="サンプルデータ：投資予定額がやや高めです。",
        details={
            "source": "sample",
            "total_amount": 1800,
            "threshold": 1500,
        },
    )

    insert_alert_event(
        conn,
        prediction_run_id=prediction_run_id,
        race_id=race2_id,
        level="warning",
        alert_type="missing_final_odds",
        message="サンプルデータ：最終オッズが未取得のレースがあります。",
        details={
            "source": "sample",
            "race_id": race2_id,
        },
    )

    conn.commit()


def count_rows(conn: sqlite3.Connection, table_name: str) -> int:
    row = conn.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
    return int(row["count"])


def print_counts(conn: sqlite3.Connection) -> None:
    print("\nCounts:")
    for table_name in TABLES_TO_COUNT:
        print(f"  {table_name}: {count_rows(conn, table_name)}")


def print_prediction_summary(conn: sqlite3.Connection) -> None:
    print("\nPrediction run summary:")

    rows = conn.execute(
        """
        SELECT
          run_key,
          target_date,
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
        WHERE run_key = ?
        ORDER BY executed_at DESC
        """,
        (SAMPLE_RUN_KEY,),
    ).fetchall()

    if not rows:
        print("  No summary rows found.")
        return

    for row in rows:
        print(f"  run_key: {row['run_key']}")
        print(f"  target_date: {row['target_date']}")
        print(f"  model_name: {row['model_name']}")
        print(f"  model_version: {row['model_version']}")
        print(f"  race_count: {row['race_count']}")
        print(f"  ticket_count: {row['ticket_count']}")
        print(f"  total_amount: {row['total_amount']}")
        print(f"  total_payout: {row['total_payout']}")
        print(f"  total_profit: {row['total_profit']}")
        print(f"  return_rate_percent: {row['return_rate_percent']}")
        print(f"  hit_rate_percent: {row['hit_rate_percent']}")


def run_foreign_key_check(conn: sqlite3.Connection) -> None:
    rows = conn.execute("PRAGMA foreign_key_check").fetchall()

    if rows:
        print("\nForeign key check: NG")
        for row in rows:
            print(dict(row))
        raise RuntimeError("Foreign key check failed.")

    print("\nForeign key check: OK")


def main() -> None:
    args = parse_args()
    db_path = args.db.resolve()

    try:
        relative_db_path = db_path.relative_to(PROJECT_ROOT)
    except ValueError:
        relative_db_path = db_path

    print(f"Database file: {relative_db_path}")

    conn = connect(db_path)

    try:
        if args.reset_data:
            delete_sample_data(conn)
            run_foreign_key_check(conn)
            print("\nSTEP 63 RESET DATA: OK")
            return

        # Make the script safe to run repeatedly.
        delete_sample_data(conn)

        print("\nSeeding sample data...")
        seed_sample_data(conn)

        print_counts(conn)
        print_prediction_summary(conn)
        run_foreign_key_check(conn)

    finally:
        conn.close()

    print("\nSTEP 63 CHECK: OK")


if __name__ == "__main__":
    main()

