#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path("db/boatrace.sqlite3")


REQUIRED_COLUMNS = {
    "prediction_tickets": {
        "amount": "INTEGER DEFAULT 0",
        "probability": "REAL DEFAULT 0.0",
        "odds": "REAL DEFAULT 0.0",
        "expected_value": "REAL DEFAULT 0.0",
        "rank": "INTEGER DEFAULT 0",
        "confidence": "REAL DEFAULT 0.0",
        "reason": "TEXT",
        "memo": "TEXT",
        "is_hit": "INTEGER DEFAULT 0",
        "payout": "INTEGER DEFAULT 0",
        "profit": "INTEGER DEFAULT 0",
    }
}


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


def show_columns(conn: sqlite3.Connection) -> None:
    print("\nCurrent prediction_tickets columns:")
    cols = get_columns(conn, "prediction_tickets")
    for col in sorted(cols):
        print(f"- {col}")


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
        conn.commit()
        show_columns(conn)
        foreign_key_check(conn)
    finally:
        conn.close()

    print("\nSTEP 78 TICKET SCHEMA PATCH: OK")


if __name__ == "__main__":
    main()
