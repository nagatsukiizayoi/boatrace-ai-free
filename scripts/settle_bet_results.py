import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("db/boatrace.sqlite3")
DEFAULT_STAKE_YEN = 100

def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def table_exists(conn, table):
    row = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)).fetchone()
    return row is not None

def columns(conn, table):
    return [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]

def normalize_ticket(value):
    if value is None:
        return ""
    return str(value).strip().replace(" ", "").replace("　", "").replace(",", "-").replace("→", "-").replace("_", "-")

def normalize_bet_type(value):
    if value is None:
        return ""
    return str(value).strip().lower()

def require_schema(conn):
    required_tables = ["prediction_tickets", "predictions", "payouts", "bet_results"]
    missing_tables = [t for t in required_tables if not table_exists(conn, t)]
    if missing_tables:
        raise SystemExit("Missing tables: " + ", ".join(missing_tables))

    checks = {
        "prediction_tickets": ["id", "prediction_id", "bet_type"],
        "predictions": ["id", "race_id"],
        "payouts": ["race_id", "bet_type", "ticket", "payout_yen"],
        "bet_results": ["prediction_ticket_id", "race_id", "bet_type", "ticket", "stake_yen", "is_hit", "payout_yen", "return_yen", "profit_yen", "return_rate"],
    }
    errors = []
    for table, required_cols in checks.items():
        existing = set(columns(conn, table))
        for col in required_cols:
            if col not in existing:
                errors.append(f"{table} missing column: {col}")
    if errors:
        print("Validation errors:")
        for e in errors:
            print("-", e)
        raise SystemExit(1)

def pick_ticket_expression(conn):
    existing = set(columns(conn, "prediction_tickets"))

    single_column_candidates = [
        "ticket",
        "ticket_text",
        "ticket_key",
        "combination",
        "boat_numbers",
        "entry_numbers",
        "predicted_ticket",
        "prediction_ticket",
        "buy_ticket",
    ]
    for col in single_column_candidates:
        if col in existing:
            return f"pt.{col}"

    triple_column_candidates = [
        ("first_boat_no", "second_boat_no", "third_boat_no"),
        ("boat1", "boat2", "boat3"),
        ("first", "second", "third"),
        ("predicted_first", "predicted_second", "predicted_third"),
        ("rank1_boat_no", "rank2_boat_no", "rank3_boat_no"),
    ]
    for a, b, c in triple_column_candidates:
        if a in existing and b in existing and c in existing:
            return f"CAST(pt.{a} AS TEXT) || '-' || CAST(pt.{b} AS TEXT) || '-' || CAST(pt.{c} AS TEXT)"

    double_column_candidates = [
        ("first_boat_no", "second_boat_no"),
        ("boat1", "boat2"),
        ("first", "second"),
        ("predicted_first", "predicted_second"),
    ]
    for a, b in double_column_candidates:
        if a in existing and b in existing:
            return f"CAST(pt.{a} AS TEXT) || '-' || CAST(pt.{b} AS TEXT)"

    raise SystemExit(
        "prediction_tickets missing ticket-like column. Existing columns: "
        + ", ".join(sorted(existing))
    )


def load_tickets(conn):
    ticket_expr = pick_ticket_expression(conn)
    sql = f"""
    SELECT
        pt.id AS prediction_ticket_id,
        p.race_id AS race_id,
        pt.bet_type AS bet_type,
        {ticket_expr} AS ticket
    FROM prediction_tickets pt
    JOIN predictions p ON p.id = pt.prediction_id
    WHERE p.race_id IS NOT NULL
      AND pt.bet_type IS NOT NULL
      AND {ticket_expr} IS NOT NULL
    ORDER BY pt.id
    """
    return conn.execute(sql).fetchall()

def load_payout_map(conn):
    rows = conn.execute("SELECT race_id, bet_type, ticket, payout_yen FROM payouts").fetchall()
    payout_map = {}
    for race_id, bet_type, ticket, payout_yen in rows:
        key = (race_id, normalize_bet_type(bet_type), normalize_ticket(ticket))
        payout_map[key] = int(payout_yen or 0)
    return payout_map

def main():
    if not DB_PATH.exists():
        raise SystemExit(f"Database not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        require_schema(conn)

        tickets = load_tickets(conn)
        if not tickets:
            raise SystemExit("No prediction tickets found. Run prediction generation first.")

        payout_map = load_payout_map(conn)
        if not payout_map:
            raise SystemExit("No payouts found. Run scripts/import_results_csv.py first.")

        timestamp = now_iso()
        conn.execute("DELETE FROM bet_results")

        hit_count = 0
        for prediction_ticket_id, race_id, bet_type, ticket in tickets:
            stake_yen = DEFAULT_STAKE_YEN
            key = (race_id, normalize_bet_type(bet_type), normalize_ticket(ticket))
            payout_yen = payout_map.get(key, 0)
            is_hit = 1 if payout_yen > 0 else 0
            return_yen = payout_yen if is_hit else 0
            profit_yen = return_yen - stake_yen
            return_rate = round(return_yen / stake_yen, 4) if stake_yen else 0.0
            hit_count += is_hit

            conn.execute("""
                INSERT INTO bet_results (
                    prediction_ticket_id, race_id, bet_type, ticket,
                    stake_yen, is_hit, payout_yen, return_yen, profit_yen, return_rate,
                    settled_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prediction_ticket_id, race_id, bet_type, ticket,
                stake_yen, is_hit, payout_yen, return_yen, profit_yen, return_rate,
                timestamp, timestamp, timestamp
            ))

        fk_errors = conn.execute("PRAGMA foreign_key_check").fetchall()
        if fk_errors:
            raise SystemExit(f"Foreign key errors: {fk_errors}")

        conn.commit()
        total = conn.execute("SELECT COUNT(*) FROM bet_results").fetchone()[0]
        print("settled bet_results:", total)
        print("hit_count:", hit_count)
        print("STEP 125 CHECK: OK")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
