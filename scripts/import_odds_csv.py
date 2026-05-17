#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


DEFAULT_DB_PATH = Path("db/boatrace.sqlite3")
DEFAULT_ODDS_CSV = Path("data/import/odds.csv")

JST = timezone(timedelta(hours=9))

ALLOWED_BET_TYPES = {
    "tansho",
    "fukusho",
    "2rentan",
    "2renfuku",
    "3rentan",
    "3renfuku",
    "kakuren",
    "unknown",
}


def now_iso() -> str:
    return datetime.now(JST).isoformat(timespec="seconds")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def to_int(value: Any, default: int | None = None) -> int | None:
    if value is None or value == "":
        return default
    return int(value)


def to_float(value: Any, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    return float(value)


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


def fallback_value_for_column(column: str, column_type: str) -> Any:
    name = column.lower()
    typ = (column_type or "").upper()

    if name == "bet_type":
        return "unknown"

    if name == "combination":
        return ""

    if name == "source":
        return "csv_step76"

    if name.endswith("_at") or name in {"created_at", "updated_at", "captured_at"}:
        return now_iso()

    if "json" in name or name in {"details", "metadata"}:
        return "{}"

    if "odds" in name or "rate" in name or "value" in name:
        return 0.0

    if "popular" in name or "rank" in name or name.endswith("_no") or name.endswith("_id"):
        return 0

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
        # id は自動採番に任せる
        if column == "id" and meta["pk"]:
            continue

        if column in values:
            insert_columns.append(column)
            insert_values.append(values[column])
            continue

        # default がある列は省略
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


def validate_row(row: dict[str, str], index: int) -> None:
    required = [
        "race_date",
        "venue_code",
        "race_no",
        "bet_type",
        "combination",
        "odds",
    ]

    missing = [key for key in required if not row.get(key)]
    if missing:
        raise ValueError(f"CSV row {index} missing required columns: {missing}")

    bet_type = row["bet_type"].strip()
    if bet_type not in ALLOWED_BET_TYPES:
        raise ValueError(
            f"CSV row {index} invalid bet_type={bet_type}. "
            f"Allowed: {sorted(ALLOWED_BET_TYPES)}"
        )

    odds = to_float(row["odds"])
    if odds is None or odds <= 0:
        raise ValueError(f"CSV row {index} odds must be positive: {row['odds']}")


def find_race_id(
    conn: sqlite3.Connection,
    race_date: str,
    venue_code: str,
    race_no: int,
) -> int:
    venue_code = str(venue_code).zfill(2)

    row = conn.execute(
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

    if row is None:
        raise RuntimeError(
            f"Race not found: race_date={race_date}, "
            f"venue_code={venue_code}, race_no={race_no}\n"
            "先に `python scripts/import_race_csv.py` を実行してください。"
        )

    return int(row["id"])


def delete_existing_source_rows(conn: sqlite3.Connection, source: str) -> None:
    if not table_exists(conn, "odds_snapshots"):
        raise RuntimeError("Table not found: odds_snapshots")

    if column_exists(conn, "odds_snapshots", "source"):
        deleted = conn.execute(
            "DELETE FROM odds_snapshots WHERE source = ?",
            (source,),
        ).rowcount
        print(f"Deleted existing odds rows for source={source}: {deleted}")
    else:
        print("odds_snapshots.source column not found. Skip source cleanup.")


def import_odds_rows(
    conn: sqlite3.Connection,
    rows: list[dict[str, str]],
    source: str,
) -> int:
    imported = 0

    for index, row in enumerate(rows, start=1):
        validate_row(row, index)

        race_date = row["race_date"].strip()
        venue_code = row["venue_code"].strip().zfill(2)
        race_no = to_int(row["race_no"])
        if race_no is None:
            raise ValueError(f"CSV row {index} race_no is required")

        race_id = find_race_id(conn, race_date, venue_code, race_no)

        bet_type = row["bet_type"].strip()
        combination = row["combination"].strip()
        odds = to_float(row["odds"])
        popularity = to_int(row.get("popularity"), None)
        captured_at = row.get("captured_at") or now_iso()
        row_source = row.get("source") or source

        values = {
            "race_id": race_id,
            "bet_type": bet_type,
            "combination": combination,
            "odds": odds,
            "popularity": popularity,
            "captured_at": captured_at,
            "source": row_source,
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }

        insert_dynamic(conn, "odds_snapshots", values)
        imported += 1

    return imported


def print_counts(conn: sqlite3.Connection) -> None:
    odds_count = conn.execute(
        "SELECT COUNT(*) AS c FROM odds_snapshots"
    ).fetchone()["c"]

    race_count = conn.execute(
        """
        SELECT COUNT(DISTINCT race_id) AS c
        FROM odds_snapshots
        """
    ).fetchone()["c"]

    print("\nImported odds summary:")
    print(f"- odds_snapshots: {odds_count}")
    print(f"- races with odds: {race_count}")

    if column_exists(conn, "odds_snapshots", "bet_type"):
        rows = conn.execute(
            """
            SELECT bet_type, COUNT(*) AS c
            FROM odds_snapshots
            GROUP BY bet_type
            ORDER BY bet_type
            """
        ).fetchall()

        print("\nOdds count by bet_type:")
        for row in rows:
            print(f"- {row['bet_type']}: {row['c']}")


def foreign_key_check(conn: sqlite3.Connection) -> None:
    rows = conn.execute("PRAGMA foreign_key_check;").fetchall()
    if rows:
        print("Foreign key check: NG")
        for row in rows:
            print(dict(row))
        raise SystemExit(1)

    print("Foreign key check: OK")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import odds CSV into SQLite database.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path")
    parser.add_argument("--odds", default=str(DEFAULT_ODDS_CSV), help="odds.csv path")
    parser.add_argument("--source", default="csv_step76", help="source name for imported rows")
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Do not delete existing odds rows for the same source before import",
    )
    args = parser.parse_args()

    db_path = Path(args.db)
    odds_csv = Path(args.odds)
    source = args.source

    print(f"Database: {db_path}")
    print(f"Odds CSV: {odds_csv}")
    print(f"Source: {source}")

    rows = read_csv(odds_csv)
    print(f"Read odds rows: {len(rows)}")

    with connect_db(db_path) as conn:
        if not table_exists(conn, "odds_snapshots"):
            raise RuntimeError("Required table not found: odds_snapshots")

        if not args.no_clean:
            delete_existing_source_rows(conn, source)

        imported = import_odds_rows(conn, rows, source)
        conn.commit()

        print(f"\nImported odds rows: {imported}")
        print_counts(conn)
        foreign_key_check(conn)

    print("\nSTEP 76 CHECK: OK")


if __name__ == "__main__":
    main()
