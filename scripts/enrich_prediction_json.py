#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


DEFAULT_DB_PATH = Path("db/boatrace.sqlite3")
DEFAULT_JSON_PATH = Path("docs/prediction.json")

JST = timezone(timedelta(hours=9))


def now_iso() -> str:
    return datetime.now(JST).isoformat(timespec="seconds")


def connect_db(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(
            f"Database not found: {db_path}\n"
            "先に DB 初期化・CSVインポート・予想生成を実行してください。"
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


def safe_json_loads(value: Any, default: Any = None) -> Any:
    if default is None:
        default = []

    if value is None:
        return default

    if isinstance(value, (list, dict)):
        return value

    text = str(value).strip()
    if not text:
        return default

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return default


def get_first_existing_column(conn: sqlite3.Connection, table: str, candidates: list[str]) -> str | None:
    cols = table_columns(conn, table)
    for col in candidates:
        if col in cols:
            return col
    return None


def fetch_prediction_score_rows(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    if not table_exists(conn, "predictions"):
        raise RuntimeError("predictions table not found")

    prediction_cols = table_columns(conn, "predictions")

    score_col = get_first_existing_column(
        conn,
        "predictions",
        [
            "scores_json",
            "features_json",
            "details_json",
            "score_json",
            "details",
            "features",
            "scores",
        ],
    )

    summary_col = get_first_existing_column(
        conn,
        "predictions",
        [
            "prediction_summary",
            "summary",
            "memo",
            "reason",
        ],
    )

    favorite_col = get_first_existing_column(
        conn,
        "predictions",
        [
            "favorite_boat_no",
            "favorite",
        ],
    )

    rival_col = get_first_existing_column(
        conn,
        "predictions",
        [
            "rival_boat_no",
            "rival",
        ],
    )

    darkhorse_col = get_first_existing_column(
        conn,
        "predictions",
        [
            "darkhorse_boat_no",
            "darkhorse",
        ],
    )

    selected_columns = [
        "p.id AS prediction_id",
        "p.race_id AS race_id",
        "r.race_date AS race_date",
        "r.race_no AS race_no",
        "v.venue_code AS venue_code",
        "v.venue_name AS venue_name",
    ]

    if "confidence" in prediction_cols:
        selected_columns.append("p.confidence AS confidence")
    else:
        selected_columns.append("NULL AS confidence")

    if "expected_value" in prediction_cols:
        selected_columns.append("p.expected_value AS expected_value")
    else:
        selected_columns.append("NULL AS expected_value")

    if "recommended_total_amount" in prediction_cols:
        selected_columns.append("p.recommended_total_amount AS recommended_total_amount")
    else:
        selected_columns.append("NULL AS recommended_total_amount")

    if score_col:
        selected_columns.append(f"p.{score_col} AS score_json")
    else:
        selected_columns.append("NULL AS score_json")

    if summary_col:
        selected_columns.append(f"p.{summary_col} AS prediction_summary")
    else:
        selected_columns.append("NULL AS prediction_summary")

    if favorite_col:
        selected_columns.append(f"p.{favorite_col} AS favorite_boat_no")
    else:
        selected_columns.append("NULL AS favorite_boat_no")

    if rival_col:
        selected_columns.append(f"p.{rival_col} AS rival_boat_no")
    else:
        selected_columns.append("NULL AS rival_boat_no")

    if darkhorse_col:
        selected_columns.append(f"p.{darkhorse_col} AS darkhorse_boat_no")
    else:
        selected_columns.append("NULL AS darkhorse_boat_no")

    sql = f"""
        SELECT
            {", ".join(selected_columns)}
        FROM predictions p
        JOIN races r ON r.id = p.race_id
        JOIN venues v ON v.id = r.venue_id
        ORDER BY r.race_date, v.venue_code, r.race_no
    """

    rows = conn.execute(sql).fetchall()
    return [dict(row) for row in rows]


def normalize_boat_no(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def normalize_score_entries(raw_score_json: Any) -> list[dict[str, Any]]:
    raw = safe_json_loads(raw_score_json, default=[])

    if isinstance(raw, dict):
        for key in ["entries", "scores", "boats", "ranking"]:
            if isinstance(raw.get(key), list):
                raw = raw[key]
                break

    if not isinstance(raw, list):
        return []

    normalized: list[dict[str, Any]] = []

    for item in raw:
        if not isinstance(item, dict):
            continue

        boat_no = normalize_boat_no(
            item.get("boat_no")
            or item.get("frame_no")
            or item.get("boat_number")
        )

        if boat_no is None:
            continue

        score = item.get("score", 0)
        try:
            score = round(float(score), 4)
        except (TypeError, ValueError):
            score = 0.0

        national_win_rate = item.get("national_win_rate", 0)
        local_win_rate = item.get("local_win_rate", 0)
        st_timing = item.get("st_timing", item.get("avg_st", 0))

        try:
            national_win_rate = round(float(national_win_rate), 3)
        except (TypeError, ValueError):
            national_win_rate = 0.0

        try:
            local_win_rate = round(float(local_win_rate), 3)
        except (TypeError, ValueError):
            local_win_rate = 0.0

        try:
            st_timing = round(float(st_timing), 3)
        except (TypeError, ValueError):
            st_timing = 0.0

        frame_no = normalize_boat_no(item.get("frame_no")) or boat_no

        normalized.append(
            {
                "rank": 0,
                "boat_no": boat_no,
                "frame_no": frame_no,
                "racer_name": item.get("racer_name") or item.get("name") or f"{boat_no}号艇",
                "racer_class": item.get("racer_class") or item.get("class") or "",
                "score": score,
                "national_win_rate": national_win_rate,
                "local_win_rate": local_win_rate,
                "st_timing": st_timing,
                "reason": build_boat_reason(
                    boat_no=boat_no,
                    frame_no=frame_no,
                    national_win_rate=national_win_rate,
                    local_win_rate=local_win_rate,
                    st_timing=st_timing,
                    score=score,
                ),
            }
        )

    normalized.sort(key=lambda x: x["score"], reverse=True)

    for index, item in enumerate(normalized, start=1):
        item["rank"] = index

    return normalized


def build_boat_reason(
    boat_no: int,
    frame_no: int,
    national_win_rate: float,
    local_win_rate: float,
    st_timing: float,
    score: float,
) -> str:
    parts = []

    if national_win_rate >= 6.0:
        parts.append("全国勝率が高い")
    elif national_win_rate >= 5.0:
        parts.append("全国勝率が安定")
    else:
        parts.append("全国勝率は控えめ")

    if local_win_rate >= 6.0:
        parts.append("当地勝率も高い")
    elif local_win_rate >= 5.0:
        parts.append("当地適性は標準以上")
    else:
        parts.append("当地勝率はやや低め")

    if st_timing and st_timing <= 0.16:
        parts.append("STが早め")
    elif st_timing and st_timing <= 0.19:
        parts.append("STは標準圏")
    else:
        parts.append("STは慎重寄り")

    if frame_no == 1:
        parts.append("1枠有利を評価")
    elif frame_no in (2, 3):
        parts.append("内寄り枠を評価")
    elif frame_no >= 5:
        parts.append("外枠のためやや割引")

    return f"{boat_no}号艇: " + "、".join(parts) + f"。総合スコア {score}"


def build_race_explanation(row: dict[str, Any], score_entries: list[dict[str, Any]]) -> dict[str, Any]:
    top = score_entries[:3]

    favorite = normalize_boat_no(row.get("favorite_boat_no"))
    rival = normalize_boat_no(row.get("rival_boat_no"))
    darkhorse = normalize_boat_no(row.get("darkhorse_boat_no"))

    if top:
        favorite = favorite or top[0]["boat_no"]
    if len(top) >= 2:
        rival = rival or top[1]["boat_no"]
    if len(top) >= 3:
        darkhorse = darkhorse or top[2]["boat_no"]

    top_text = []
    labels = ["本命", "対抗", "三番手"]
    for label, item in zip(labels, top):
        top_text.append(
            f'{label}: {item["boat_no"]}号艇 {item["racer_name"]} '
            f'(score={item["score"]})'
        )

    explanation = {
        "favorite_boat_no": favorite,
        "rival_boat_no": rival,
        "darkhorse_boat_no": darkhorse,
        "confidence": row.get("confidence"),
        "expected_value": row.get("expected_value"),
        "recommended_total_amount": row.get("recommended_total_amount"),
        "summary": row.get("prediction_summary") or "簡易スコアに基づく予想です。",
        "score_method": {
            "name": "simple_rule_score_v1",
            "description": "全国勝率、当地勝率、ST、枠番補正を組み合わせた簡易スコアです。",
            "weights": {
                "national_win_rate": 0.65,
                "local_win_rate": 0.35,
                "frame_bonus": "1枠を最も評価し、外枠はやや割引",
                "st_bonus": "0.15付近のSTを高評価",
            },
        },
        "top_summary": top_text,
        "score_details": score_entries,
    }

    return explanation


def get_race_key_from_db_row(row: dict[str, Any]) -> tuple[str, str, int]:
    return (
        str(row.get("race_date") or ""),
        str(row.get("venue_code") or "").zfill(2),
        int(row.get("race_no") or 0),
    )


def get_race_key_from_json_race(data: dict[str, Any], race: dict[str, Any]) -> tuple[str, str, int] | None:
    race_date = (
        race.get("race_date")
        or race.get("date")
        or race.get("target_date")
        or data.get("target_date")
        or ""
    )

    venue_code = (
        race.get("venue_code")
        or race.get("jcd")
        or race.get("venueId")
        or ""
    )

    venue = race.get("venue")
    if isinstance(venue, dict):
        venue_code = venue_code or venue.get("code") or venue.get("venue_code") or ""

    race_no = (
        race.get("race_no")
        or race.get("raceNo")
        or race.get("race_number")
        or race.get("race")
        or 0
    )

    try:
        race_no_int = int(race_no)
    except (TypeError, ValueError):
        return None

    if not race_date or not race_no_int:
        return None

    return (str(race_date), str(venue_code).zfill(2), race_no_int)


def enrich_json(data: dict[str, Any], prediction_rows: list[dict[str, Any]]) -> dict[str, Any]:
    explanations_by_full_key: dict[tuple[str, str, int], dict[str, Any]] = {}
    explanations_by_race_no: dict[int, dict[str, Any]] = {}

    for row in prediction_rows:
        score_entries = normalize_score_entries(row.get("score_json"))
        explanation = build_race_explanation(row, score_entries)

        full_key = get_race_key_from_db_row(row)
        explanations_by_full_key[full_key] = explanation
        explanations_by_race_no[full_key[2]] = explanation

    races = data.get("races")
    if not isinstance(races, list):
        raise RuntimeError("prediction.json の races が list ではありません")

    enriched_count = 0

    for race in races:
        if not isinstance(race, dict):
            continue

        key = get_race_key_from_json_race(data, race)
        explanation = None

        if key is not None:
            explanation = explanations_by_full_key.get(key)

            # venue_codeがJSON側に無い場合の救済
            if explanation is None:
                explanation = explanations_by_race_no.get(key[2])

        if explanation is None:
            continue

        race["score_explanation"] = explanation
        race["score_details"] = explanation["score_details"]
        race["score_method"] = explanation["score_method"]

        if "prediction_summary" not in race or not race.get("prediction_summary"):
            race["prediction_summary"] = explanation["summary"]

        enriched_count += 1

    data["explainability"] = {
        "enabled": True,
        "generated_at": now_iso(),
        "method": "simple_rule_score_v1",
        "enriched_race_count": enriched_count,
        "description": "CSV出走表から生成した簡易予想に、スコア詳細と予想理由を追加しています。",
    }

    return data


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Enrich docs/prediction.json with score explanations from SQLite DB."
    )
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path")
    parser.add_argument("--json", default=str(DEFAULT_JSON_PATH), help="prediction.json path")
    args = parser.parse_args()

    db_path = Path(args.db)
    json_path = Path(args.json)

    if not json_path.exists():
        raise FileNotFoundError(
            f"prediction.json not found: {json_path}\n"
            "先に `python scripts/export_prediction_json.py` を実行してください。"
        )

    print(f"Database: {db_path}")
    print(f"Prediction JSON: {json_path}")

    data = json.loads(json_path.read_text(encoding="utf-8"))

    with connect_db(db_path) as conn:
        prediction_rows = fetch_prediction_score_rows(conn)

    if not prediction_rows:
        raise SystemExit("No predictions found in database")

    enriched = enrich_json(data, prediction_rows)

    json_path.write_text(
        json.dumps(enriched, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    races = enriched.get("races") or []
    enriched_count = enriched.get("explainability", {}).get("enriched_race_count", 0)

    print(f"Total races in JSON: {len(races)}")
    print(f"Enriched races: {enriched_count}")

    if enriched_count == 0:
        raise SystemExit("No races were enriched. JSON race keys may not match DB races.")

    print("\nSTEP 72 CHECK: OK")


if __name__ == "__main__":
    main()
