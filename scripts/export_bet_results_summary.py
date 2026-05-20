import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("db/boatrace.sqlite3")
OUT_PATH = Path("docs/bet_results_summary.json")

def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def table_exists(conn, table):
    row = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)).fetchone()
    return row is not None

def main():
    if not DB_PATH.exists():
        raise SystemExit(f"Database not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        if not table_exists(conn, "bet_results"):
            raise SystemExit("Missing table: bet_results")

        total = conn.execute("SELECT COUNT(*) FROM bet_results").fetchone()[0]
        if total < 1:
            raise SystemExit("No bet_results rows found. Run scripts/settle_bet_results.py first.")

        summary = conn.execute("""
            SELECT
                COUNT(*) AS total_bets,
                SUM(CASE WHEN is_hit = 1 THEN 1 ELSE 0 END) AS hit_count,
                COALESCE(SUM(stake_yen), 0) AS total_stake_yen,
                COALESCE(SUM(return_yen), 0) AS total_return_yen,
                COALESCE(SUM(profit_yen), 0) AS total_profit_yen,
                MAX(settled_at) AS latest_settled_at
            FROM bet_results
        """).fetchone()

        by_type_rows = conn.execute("""
            SELECT
                bet_type,
                COUNT(*) AS total_bets,
                SUM(CASE WHEN is_hit = 1 THEN 1 ELSE 0 END) AS hit_count,
                COALESCE(SUM(stake_yen), 0) AS total_stake_yen,
                COALESCE(SUM(return_yen), 0) AS total_return_yen,
                COALESCE(SUM(profit_yen), 0) AS total_profit_yen
            FROM bet_results
            GROUP BY bet_type
            ORDER BY bet_type
        """).fetchall()

        recent_rows = conn.execute("""
            SELECT prediction_ticket_id, race_id, bet_type, ticket, stake_yen, is_hit,
                   payout_yen, return_yen, profit_yen, return_rate, settled_at
            FROM bet_results
            ORDER BY id DESC
            LIMIT 10
        """).fetchall()

        total_bets = int(summary["total_bets"] or 0)
        hit_count = int(summary["hit_count"] or 0)
        total_stake = int(summary["total_stake_yen"] or 0)
        total_return = int(summary["total_return_yen"] or 0)
        total_profit = int(summary["total_profit_yen"] or 0)
        hit_rate = round(hit_count / total_bets, 4) if total_bets else 0.0
        return_rate = round(total_return / total_stake, 4) if total_stake else 0.0

        data = {
            "generated_at": now_iso(),
            "source": "db/boatrace.sqlite3:bet_results",
            "summary": {
                "total_bets": total_bets,
                "hit_count": hit_count,
                "miss_count": total_bets - hit_count,
                "hit_rate": hit_rate,
                "total_stake_yen": total_stake,
                "total_return_yen": total_return,
                "total_profit_yen": total_profit,
                "return_rate": return_rate,
                "latest_settled_at": summary["latest_settled_at"],
            },
            "by_bet_type": [],
            "recent_results": [],
        }

        for row in by_type_rows:
            stake = int(row["total_stake_yen"] or 0)
            ret = int(row["total_return_yen"] or 0)
            bets = int(row["total_bets"] or 0)
            hits = int(row["hit_count"] or 0)
            data["by_bet_type"].append({
                "bet_type": row["bet_type"],
                "total_bets": bets,
                "hit_count": hits,
                "hit_rate": round(hits / bets, 4) if bets else 0.0,
                "total_stake_yen": stake,
                "total_return_yen": ret,
                "total_profit_yen": int(row["total_profit_yen"] or 0),
                "return_rate": round(ret / stake, 4) if stake else 0.0,
            })

        for row in recent_rows:
            data["recent_results"].append(dict(row))

        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        print("bet_results summary exported:", OUT_PATH)
        print("total_bets:", total_bets)
        print("hit_count:", hit_count)
        print("return_rate:", return_rate)
        print("STEP 128 CHECK: OK")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
