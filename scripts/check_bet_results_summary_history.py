import json
from pathlib import Path

HISTORY_PATH = Path("docs/bet_results_summary_history.json")

REQUIRED_TOP_KEYS = ["generated_at", "source", "summary", "history"]
REQUIRED_SUMMARY_KEYS = ["snapshot_count", "max_snapshots", "latest_generated_at"]
REQUIRED_SNAPSHOT_KEYS = [
    "snapshot_id",
    "generated_at",
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

def as_int(value):
    return int(value or 0)

def as_float(value):
    return float(value or 0)

def approx_equal(a, b, tolerance=0.0001):
    return abs(float(a) - float(b)) <= tolerance

def validate_snapshot(row, index):
    errors = []
    if not isinstance(row, dict):
        return [f"history[{index}] must be an object"]

    for key in REQUIRED_SNAPSHOT_KEYS:
        if key not in row:
            errors.append(f"history[{index}] missing key: {key}")

    total_bets = as_int(row.get("total_bets"))
    hit_count = as_int(row.get("hit_count"))
    miss_count = as_int(row.get("miss_count"))
    hit_rate = as_float(row.get("hit_rate"))
    total_stake = as_int(row.get("total_stake_yen"))
    total_return = as_int(row.get("total_return_yen"))
    total_profit = as_int(row.get("total_profit_yen"))
    return_rate = as_float(row.get("return_rate"))

    if not row.get("snapshot_id"):
        errors.append(f"history[{index}].snapshot_id is required")
    if not row.get("generated_at"):
        errors.append(f"history[{index}].generated_at is required")
    if not row.get("latest_settled_at"):
        errors.append(f"history[{index}].latest_settled_at is required")

    if total_bets < 1:
        errors.append(f"history[{index}].total_bets must be >= 1")
    if hit_count < 0 or miss_count < 0:
        errors.append(f"history[{index}] hit_count and miss_count must be >= 0")
    if total_stake < 1:
        errors.append(f"history[{index}].total_stake_yen must be >= 1")
    if total_return < 0:
        errors.append(f"history[{index}].total_return_yen must be >= 0")

    if total_bets != hit_count + miss_count:
        errors.append(f"history[{index}].total_bets must equal hit_count + miss_count")
    if total_profit != total_return - total_stake:
        errors.append(f"history[{index}].total_profit_yen must equal total_return_yen - total_stake_yen")

    expected_hit_rate = round(hit_count / total_bets, 4) if total_bets else 0.0
    expected_return_rate = round(total_return / total_stake, 4) if total_stake else 0.0

    if not approx_equal(hit_rate, expected_hit_rate):
        errors.append(f"history[{index}].hit_rate mismatch: expected {expected_hit_rate}, got {hit_rate}")
    if not approx_equal(return_rate, expected_return_rate):
        errors.append(f"history[{index}].return_rate mismatch: expected {expected_return_rate}, got {return_rate}")

    return errors

def main():
    errors = []

    if not HISTORY_PATH.exists():
        raise SystemExit(f"Missing file: {HISTORY_PATH}")

    try:
        data = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        raise SystemExit(f"Invalid JSON: {e}")

    if not isinstance(data, dict):
        raise SystemExit("JSON root must be an object")

    for key in REQUIRED_TOP_KEYS:
        if key not in data:
            errors.append(f"Missing top-level key: {key}")

    summary = data.get("summary")
    history = data.get("history")

    if not isinstance(summary, dict):
        errors.append("summary must be an object")
        summary = {}

    if not isinstance(history, list):
        errors.append("history must be a list")
        history = []

    for key in REQUIRED_SUMMARY_KEYS:
        if key not in summary:
            errors.append(f"Missing summary key: {key}")

    snapshot_count = as_int(summary.get("snapshot_count"))
    max_snapshots = as_int(summary.get("max_snapshots"))

    if snapshot_count != len(history):
        errors.append(f"summary.snapshot_count must equal len(history): expected {len(history)}, got {snapshot_count}")
    if snapshot_count < 1:
        errors.append("summary.snapshot_count must be >= 1")
    if max_snapshots < 1:
        errors.append("summary.max_snapshots must be >= 1")
    if max_snapshots and snapshot_count > max_snapshots:
        errors.append("summary.snapshot_count must be <= max_snapshots")
    if not summary.get("latest_generated_at"):
        errors.append("summary.latest_generated_at is required")

    seen_ids = set()
    generated_values = []

    for i, row in enumerate(history):
        errors.extend(validate_snapshot(row, i))
        if isinstance(row, dict):
            sid = row.get("snapshot_id")
            if sid in seen_ids:
                errors.append(f"duplicate snapshot_id: {sid}")
            if sid:
                seen_ids.add(sid)
            generated_values.append(row.get("generated_at"))

    if history and summary.get("latest_generated_at") != history[-1].get("generated_at"):
        errors.append("summary.latest_generated_at must equal latest history generated_at")

    print("bet_results summary history:")
    print("  snapshot_count:", snapshot_count)
    print("  max_snapshots:", max_snapshots)
    print("  latest_generated_at:", summary.get("latest_generated_at"))
    if history:
        latest = history[-1]
        print("  latest_snapshot_id:", latest.get("snapshot_id"))
        print("  latest_total_bets:", latest.get("total_bets"))
        print("  latest_return_rate:", latest.get("return_rate"))

    if errors:
        print("Validation errors:")
        for e in errors:
            print("-", e)
        raise SystemExit(1)

    print("Bet results summary history validation: OK")
    print("STEP 139 CHECK: OK")

if __name__ == "__main__":
    main()
