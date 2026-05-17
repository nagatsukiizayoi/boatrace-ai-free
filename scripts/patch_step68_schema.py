#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path("db/boatrace.sqlite3")


REQUIRED_COLUMNS = {
    "races": {
        "race_name": "TEXT",
        "grade": "TEXT",
        "distance": "INTEGER",
        "deadline_at": "TEXT",
        "start_time": "TEXT",
        "weather": "TEXT",
        "wind_direction": "TEXT",
        "wind_speed": "REAL",
        "water_temperature": "REAL",
        "wave_height": "INTEGER",
        "status": "TEXT",
    },
    "racers": {
        "racer_registration_no": "TEXT",
        "registration_no": "TEXT",
        "racer_name": "TEXT",
        "racer_class": "TEXT",
        "branch": "TEXT",
        "age": "INTEGER",
        "weight": "REAL",
        "national_win_rate": "REAL",
        "local_win_rate": "REAL",
    },
    "race_entries": {
        "boat_no": "INTEGER",
        "motor_no": "INTEGER",
        "boat_number": "INTEGER",
        "national_win_rate": "REAL",
        "local_win_rate": "REAL",
        "st_course": "INTEGER",
        "st_timing": "REAL",
    },
}


REQUIRED_INDEXES = [
    {
        "name": "ux_racers_racer_registration_no",
        "sql": """
            CREATE UNIQUE INDEX IF NOT EXISTS ux_racers_racer_registration_no
            ON racers(racer_registration_no)
        """,
    },
    {
        "name": "ux_racers_registration_no",
        "sql": """
            CREATE UNIQUE INDEX IF NOT EXISTS ux_racers_registration_no
            ON racers(registration_no)
        """,
    },
    {
        "name": "ux_venues_venue_code",
        "sql": """
            CREATE UNIQUE INDEX IF NOT EXISTS ux_venues_venue_code
            ON venues(venue_code)
        """,
    },
]


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


def get_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table});").fetchall()
    return {row[1] for row in rows}


def add_missing_columns(conn: sqlite3.Connection) -> None:
    for table, columns in REQUIRED_COLUMNS.items():
        if not table_exists(conn, table):
            raise RuntimeError(f"Table not found: {table}")

        existing = get_columns(conn, table)

        for column_name, column_type in columns.items():
            if column_name in existing:
                print(f"OK   {table}.{column_name} already exists")
                continue

            sql = f"ALTER TABLE {table} ADD COLUMN {column_name} {column_type};"
            print(f"ADD  {table}.{column_name} {column_type}")
            conn.execute(sql)


def add_required_indexes(conn: sqlite3.Connection) -> None:
    print("\nChecking indexes:")
    for item in REQUIRED_INDEXES:
        name = item["name"]
        sql = item["sql"]
        print(f"OK   create index if not exists: {name}")
        conn.execute(sql)


def show_table_columns(conn: sqlite3.Connection) -> None:
    print("\nCurrent columns:")
    for table in REQUIRED_COLUMNS:
        cols = sorted(get_columns(conn, table))
        print(f"- {table}: {', '.join(cols)}")


def foreign_key_check(conn: sqlite3.Connection) -> None:
    rows = conn.execute("PRAGMA foreign_key_check;").fetchall()
    if rows:
        print("Foreign key check: NG")
        for row in rows:
            print(row)
        raise SystemExit(1)

    print("\nForeign key check: OK")


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(
            f"Database not found: {DB_PATH}\n"
            "先に `python scripts/init_db.py --reset` を実行してください。"
        )

    print(f"Database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)

    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        add_missing_columns(conn)
        add_required_indexes(conn)
        conn.commit()
        show_table_columns(conn)
        foreign_key_check(conn)
    finally:
        conn.close()

    print("\nSTEP 68 SCHEMA PATCH: OK")


if __name__ == "__main__":
    main()
