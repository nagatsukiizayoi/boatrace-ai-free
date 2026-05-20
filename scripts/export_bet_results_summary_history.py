import json
from datetime import datetime, timezone
from pathlib import Path

SUMMARY_PATH = Path("docs/bet_results_summary.json")
HISTORY_PATH = Path("docs/bet_results_summary_history.json")
MAX_SNAPSHOTS = 50

def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def safe_int(value):
    return int(value or 0)

def safe_float(value):
    return float(value or 0)

def load_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))

def make_snapshot_id(generated_at):
    cleaned = str(generated_at or now_iso())
    cleaned = cleaned.replace("-", "").replace(":", "").replace("+", "").replace("T", "").replace("Z", "")
    cleaned = cleaned.replace(".", "").replace(" ", "")
    return "bet-results-" + cleaned[:14]

def snapshot_from_summary(summary_data):
    summary = summary_data.get("summary") or {}
    generated_at = summary_data.get("generated_at") or now_iso()

    total_bets = safe_int(summary.get("total_bets"))
    hit_count = safe_int(summary.get("hit_count"))
    miss_count = safe_int(summary.get("miss_count"))
    total_stake = safe_int(summary.get("total_stake_yen"))
    total_return = safe_int(summary.get("total_return_yen"))
    total_profit = safe_int(summary.get("total_profit_yen"))

    return {
        "snapshot_id": make_snapshot_id(generated_at),
        "generated_at": generated_at,
        "total_bets": total_bets,
        "hit_count": hit_count,
        "miss_count": miss_count,
        "hit_rate": safe_float(summary.get("hit_rate")),
        "total_stake_yen": total_stake,
        "total_return_yen": total_return,
        "total_profit_yen": total_profit,
        "return_rate": safe_float(summary.get("return_rate")),
        "latest_settled_at": summary.get("latest_settled_at"),
    }

def same_snapshot(a, b):
    keys = [
        "total_bets",
        "hit_count",
        "miss_count",
        "hit_rate",
        "total_stake_yen",
        "total_return_yen",
        "total_profit_yen",
        "return_rate",
        "latest_settled_at",
    ]
    return all(a.get(k) == b.get(k) for k in keys)

def validate_snapshot(snapshot):
    errors = []
    total_bets = safe_int(snapshot.get("total_bets"))
    hit_count = safe_int(snapshot.get("hit_count"))
    miss_count = safe_int(snapshot.get("miss_count"))
    total_stake = safe_int(snapshot.get("total_stake_yen"))
    total_return = safe_int(snapshot.get("total_return_yen"))
    total_profit = safe_int(snapshot.get("total_profit_yen"))

    if total_bets < 1:
        errors.append("snapshot.total_bets must be >= 1")
    if total_bets != hit_count + miss_count:
        errors.append("snapshot.total_bets must equal hit_count + miss_count")
    if total_stake < 1:
        errors.append("snapshot.total_stake_yen must be >= 1")
    if total_return < 0:
        errors.append("snapshot.total_return_yen must be >= 0")
    if total_profit != total_return - total_stake:
        errors.append("snapshot.total_profit_yen must equal total_return_yen - total_stake_yen")
    if not snapshot.get("latest_settled_at"):
        errors.append("snapshot.latest_settled_at is required")
    return errors

def main():
    if not SUMMARY_PATH.exists():
        raise SystemExit(f"Missing file: {SUMMARY_PATH}")

    summary_data = load_json(SUMMARY_PATH)
    if not isinstance(summary_data, dict):
        raise SystemExit("bet_results_summary.json root must be an object")

    snapshot = snapshot_from_summary(summary_data)
    errors = validate_snapshot(snapshot)
    if errors:
        print("Validation errors:")
        for e in errors:
            print("-", e)
        raise SystemExit(1)

def same_snapshot(a, b):
    keys = [
        "total_bets",
        "hit_count",
        "miss_count",
        "hit_rate",
        "total_stake_yen",
        "total_return_yen",
        "total_profit_yen",
        "return_rate",
        "latest_settled_at",
    ]
    return all(a.get(k) == b.get(k) for k in keys)

def validate_snapshot(snapshot):
    errors = []
    total_bets = safe_int(snapshot.get("total_bets"))
    hit_count = safe_int(snapshot.get("hit_count"))
    miss_count = safe_int(snapshot.get("miss_count"))
    total_stake = safe_int(snapshot.get("total_stake_yen"))
    total_return = safe_int(snapshot.get("total_return_yen"))
    total_profit = safe_int(snapshot.get("total_profit_yen"))

    if total_bets < 1:
        errors.append("snapshot.total_bets must be >= 1")
    if total_bets != hit_count + miss_count:
        errors.append("snapshot.total_bets must equal hit_count + miss_count")
    if total_stake < 1:
        errors.append("snapshot.total_stake_yen must be >= 1")
    if total_return < 0:
        errors.append("snapshot.total_return_yen must be >= 0")
    if total_profit != total_return - total_stake:
        errors.append("snapshot.total_profit_yen must equal total_return_yen - total_stake_yen")
    if not snapshot.get("latest_settled_at"):
        errors.append("snapshot.latest_settled_at is required")
    return errors

def main():
    if not SUMMARY_PATH.exists():
        raise SystemExit(f"Missing file: {SUMMARY_PATH}")

    summary_data = load_json(SUMMARY_PATH)
    if not isinstance(summary_data, dict):
        raise SystemExit("bet_results_summary.json root must be an object")

    snapshot = snapshot_from_summary(summary_data)
    errors = validate_snapshot(snapshot)
    if errors:
        print("Validation errors:")
        for e in errors:
            print("-", e)
        raise SystemExit(1)

    existing = load_json(HISTORY_PATH)
    if isinstance(existing, dict) and isinstance(existing.get("history"), list):
        history = existing.get("history")
    else:
        history = []

    appended = False
    if not history or not same_snapshot(history[-1], snapshot):
        history.append(snapshot)
        appended = True

    if len(history) > MAX_SNAPSHOTS:
        history = history[-MAX_SNAPSHOTS:]

    generated_at = now_iso()
    data = {
        "generated_at": generated_at,
        "source": str(SUMMARY_PATH),
        "summary": {
            "snapshot_count": len(history),
            "max_snapshots": MAX_SNAPSHOTS,
            "latest_generated_at": history[-1].get("generated_at") if history else None,
        },
        "history": history,
    }

    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("bet_results summary history exported:", HISTORY_PATH)
    print("snapshot_count:", len(history))
    print("appended:", appended)
    print("latest_snapshot_id:", history[-1].get("snapshot_id") if history else "-")
    print("STEP 138 CHECK: OK")

if __name__ == "__main__":
    main()
