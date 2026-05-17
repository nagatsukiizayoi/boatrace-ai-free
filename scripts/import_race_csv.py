#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path
from typing import Any


DEFAULT_DB_PATH = Path("db/boatrace.sqlite3")
DEFAULT_RACES_CSV = Path("data/import/races.csv")
DEFAULT_ENTRIES_CSV = Path("data/import/race_entries.csv")


VENUE_NAMES = {
    "01": "桐生",
    "02": "戸田",
    "03": "江戸川",
    "04": "平和島",
    "05": "多摩川",
    "06": "浜名湖",
    "07": "蒲郡",
    "08": "常滑",
    "09": "津",
    "10": "三国",
    "11": "びわこ",
    "12": "住之江",
    "13": "尼崎",
    "14": "鳴門",
    "15": "丸亀",
    "16": "児島",
    "17": "宮島",
    "18": "徳山",
    "19": "下関",
    "20": "若松",
    "21": "芦屋",
    "22": "福岡",
    "23": "唐津",
    "24": "大村",
}


def to_int(value: Any, default: int | None = None) -> int | None:
    if value is None or value == "":
        return default
    return int(value)


def to_float(value: Any, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    return float(value)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


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


def ensure_venue(conn: sqlite3.Connection, venue_code: str) -> int:
    venue_code = str(venue_code).zfill(2)
    venue_name = VENUE_NAMES.get(venue_code, f"会場{venue_code}")

    conn.execute(
        """
        INSERT INTO venues (
            venue_code,
            venue_name,
            region,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT(venue_code) DO UPDATE SET
            venue_name = excluded.venue_name,
            updated_at = CURRENT_TIMESTAMP
        """,
        (venue_code, venue_name, ""),
    )

    row = conn.execute(
        "SELECT id FROM venues WHERE venue_code = ?",
        (venue_code,),
    ).fetchone()

    if row is None:
        raise RuntimeError(f"Failed to get venue id: {venue_code}")

    return int(row["id"])


def upsert_race(conn: sqlite3.Connection, row: dict[str, str]) -> int:
    venue_id = ensure_venue(conn, row["venue_code"])

    race_date = row["race_date"]
    race_no = to_int(row["race_no"])
    if race_no is None:
        raise ValueError("race_no is required")

    conn.execute(
        """
        INSERT INTO races (
            race_date,
            venue_id,
            race_no,
            race_name,
            grade,
            distance,
            deadline_at,
            start_time,
            weather,
            wind_direction,
            wind_speed,
            water_temperature,
            wave_height,
            status,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT(race_date, venue_id, race_no) DO UPDATE SET
            race_name = excluded.race_name,
            grade = excluded.grade,
            distance = excluded.distance,
            deadline_at = excluded.deadline_at,
            start_time = excluded.start_time,
            weather = excluded.weather,
            wind_direction = excluded.wind_direction,
            wind_speed = excluded.wind_speed,
            water_temperature = excluded.water_temperature,
            wave_height = excluded.wave_height,
            status = excluded.status,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            race_date,
            venue_id,
            race_no,
            row.get("race_name") or "",
            row.get("grade") or "",
            to_int(row.get("distance"), 1800),
            row.get("deadline_at") or None,
            row.get("start_time") or None,
            row.get("weather") or None,
            row.get("wind_direction") or None,
            to_float(row.get("wind_speed")),
            to_float(row.get("water_temperature")),
            to_int(row.get("wave_height")),
            row.get("status") or "scheduled",
        ),
    )

    found = conn.execute(
        """
        SELECT id
        FROM races
        WHERE race_date = ?
          AND venue_id = ?
          AND race_no = ?
        """,
        (race_date, venue_id, race_no),
    ).fetchone()

    if found is None:
        raise RuntimeError(f"Failed to get race id: {race_date} {venue_id} {race_no}")

    return int(found["id"])


def ensure_racer(conn: sqlite3.Connection, row: dict[str, str]) -> int:
    registration_no = str(row["registration_no"]).strip()
    if not registration_no:
        raise ValueError("registration_no is required")

    table_columns = {
        info["name"]
        for info in conn.execute("PRAGMA table_info(racers);").fetchall()
    }

    # 現在の schema では racer_registration_no が本来の必須列。
    # ただし過去の互換用に registration_no が存在する場合は両方に入れる。
    if "racer_registration_no" in table_columns:
        conflict_column = "racer_registration_no"
    elif "registration_no" in table_columns:
        conflict_column = "registration_no"
    else:
        raise RuntimeError(
            "racers table must have racer_registration_no or registration_no column"
        )

    values_by_column = {
        "racer_registration_no": registration_no,
        "registration_no": registration_no,
        "racer_name": row.get("racer_name") or "",
        "racer_class": row.get("racer_class") or "",
        "branch": row.get("branch") or "",
        "age": to_int(row.get("age")),
        "weight": to_float(row.get("weight")),
        "national_win_rate": to_float(row.get("national_win_rate")),
        "local_win_rate": to_float(row.get("local_win_rate")),
    }

    insert_columns: list[str] = []
    insert_values: list[object] = []

    preferred_order = [
        "racer_registration_no",
        "registration_no",
        "racer_name",
        "racer_class",
        "branch",
        "age",
        "weight",
        "national_win_rate",
        "local_win_rate",
    ]

    for column in preferred_order:
        if column in table_columns:
            insert_columns.append(column)
            insert_values.append(values_by_column[column])

    if "created_at" in table_columns:
        insert_columns.append("created_at")
        insert_values.append(None)

    if "updated_at" in table_columns:
        insert_columns.append("updated_at")
        insert_values.append(None)

    placeholders = []
    actual_values = []

    for column, value in zip(insert_columns, insert_values):
        if column in {"created_at", "updated_at"}:
            placeholders.append("CURRENT_TIMESTAMP")
        else:
            placeholders.append("?")
            actual_values.append(value)

    update_columns = [
        column
        for column in insert_columns
        if column not in {conflict_column, "created_at"}
    ]

    update_assignments = []
    for column in update_columns:
        if column == "updated_at":
            update_assignments.append("updated_at = CURRENT_TIMESTAMP")
        else:
            update_assignments.append(f"{column} = excluded.{column}")

    if update_assignments:
        conflict_clause = (
            f"ON CONFLICT({conflict_column}) DO UPDATE SET "
            + ", ".join(update_assignments)
        )
    else:
        conflict_clause = f"ON CONFLICT({conflict_column}) DO NOTHING"

    sql = f"""
        INSERT INTO racers (
            {", ".join(insert_columns)}
        )
        VALUES (
            {", ".join(placeholders)}
        )
        {conflict_clause}
    """

    conn.execute(sql, actual_values)

    found = conn.execute(
        f"SELECT id FROM racers WHERE {conflict_column} = ?",
        (registration_no,),
    ).fetchone()

    if found is None and "registration_no" in table_columns:
        found = conn.execute(
            "SELECT id FROM racers WHERE registration_no = ?",
            (registration_no,),
        ).fetchone()

    if found is None:
        raise RuntimeError(f"Failed to get racer id: {registration_no}")

    return int(found["id"])

def find_race_id(
    conn: sqlite3.Connection,
    race_date: str,
    venue_code: str,
    race_no: int,
) -> int:
    venue_code = str(venue_code).zfill(2)

    found = conn.execute(
        """
        SELECT r.id
        FROM races r
        JOIN venues v ON v.id = r.venue_id
        WHERE r.race_date = ?
          AND v.venue_code = ?
          AND r.race_no = ?
        """,
        (race_date, venue_code, race_no),
    ).fetchone()

    if found is None:
        raise RuntimeError(
            f"Race not found for entry: date={race_date}, venue_code={venue_code}, race_no={race_no}"
        )

    return int(found["id"])


def upsert_entry(conn: sqlite3.Connection, row: dict[str, str]) -> int:
    race_no = to_int(row["race_no"])
    frame_no = to_int(row["frame_no"])

    if race_no is None:
        raise ValueError("race_no is required")
    if frame_no is None:
        raise ValueError("frame_no is required")

    race_id = find_race_id(
        conn,
        row["race_date"],
        row["venue_code"],
        race_no,
    )
    racer_id = ensure_racer(conn, row)

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
            local_win_rate,
            st_course,
            st_timing,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT(race_id, frame_no) DO UPDATE SET
            racer_id = excluded.racer_id,
            boat_no = excluded.boat_no,
            motor_no = excluded.motor_no,
            boat_number = excluded.boat_number,
            national_win_rate = excluded.national_win_rate,
            local_win_rate = excluded.local_win_rate,
            st_course = excluded.st_course,
            st_timing = excluded.st_timing,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            race_id,
            racer_id,
            frame_no,
            frame_no,
            to_int(row.get("motor_no")),
            to_int(row.get("boat_no")),
            to_float(row.get("national_win_rate")),
            to_float(row.get("local_win_rate")),
            to_int(row.get("st_course")),
            to_float(row.get("st_timing")),
        ),
    )

    found = conn.execute(
        """
        SELECT id
        FROM race_entries
        WHERE race_id = ?
          AND frame_no = ?
        """,
        (race_id, frame_no),
    ).fetchone()

    if found is None:
        raise RuntimeError(f"Failed to get entry id: race_id={race_id}, frame_no={frame_no}")

    return int(found["id"])


def print_counts(conn: sqlite3.Connection) -> None:
    tables = ["venues", "races", "racers", "race_entries"]
    print("\nImported table counts:")
    for table in tables:
        count = conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"]
        print(f"- {table}: {count}")


def foreign_key_check(conn: sqlite3.Connection) -> None:
    rows = conn.execute("PRAGMA foreign_key_check;").fetchall()
    if rows:
        print("Foreign key check: NG")
        for row in rows:
            print(dict(row))
        raise SystemExit(1)

    print("Foreign key check: OK")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import race CSV files into SQLite database.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path")
    parser.add_argument("--races", default=str(DEFAULT_RACES_CSV), help="races.csv path")
    parser.add_argument("--entries", default=str(DEFAULT_ENTRIES_CSV), help="race_entries.csv path")
    args = parser.parse_args()

    db_path = Path(args.db)
    races_csv = Path(args.races)
    entries_csv = Path(args.entries)

    print(f"Database: {db_path}")
    print(f"Races CSV: {races_csv}")
    print(f"Entries CSV: {entries_csv}")

    race_rows = read_csv(races_csv)
    entry_rows = read_csv(entries_csv)

    print(f"Read races: {len(race_rows)}")
    print(f"Read entries: {len(entry_rows)}")

    with connect_db(db_path) as conn:
        for row in race_rows:
            upsert_race(conn, row)

        for row in entry_rows:
            upsert_entry(conn, row)

        conn.commit()

        print_counts(conn)
        foreign_key_check(conn)

    print("\nSTEP 68 CHECK: OK")


if __name__ == "__main__":
    main()
