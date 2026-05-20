import json
from pathlib import Path

INDEX_PATH = Path("docs/index.html")
HISTORY_PATH = Path("docs/bet_results_summary_history.json")

REQUIRED_HTML_TOKENS = [
    "STEP142_BET_RESULTS_TREND_HISTORY_STYLE",
    "STEP142_BET_RESULTS_TREND_HISTORY_HTML",
    "STEP142_BET_RESULTS_TREND_HISTORY_SCRIPT",
    "step142BetResultsTrendPanel",
    "的中判定トレンド",
    "bet_results_summary_history.json",
    "OK: 的中判定トレンドを表示しました",
]

REQUIRED_TOP_KEYS = ["generated_at", "source", "summary", "history"]
REQUIRED_SUMMARY_KEYS = ["snapshot_count", "max_snapshots", "latest_generated_at"]
REQUIRED_LATEST_KEYS = [
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

def main():
    errors = []

    if not INDEX_PATH.exists():
        errors.append(f"Missing file: {INDEX_PATH}")
    if not HISTORY_PATH.exists():
        errors.append(f"Missing file: {HISTORY_PATH}")

    if INDEX_PATH.exists():
        html = INDEX_PATH.read_text(encoding="utf-8")
        for token in REQUIRED_HTML_TOKENS:
            if token not in html:
                errors.append(f"Missing HTML token: {token}")

    data = None
    if HISTORY_PATH.exists():
        try:
            data = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append(f"Invalid JSON: {e}")

    if isinstance(data, dict):
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

        if snapshot_count < 1:
            errors.append("summary.snapshot_count must be >= 1")
        if snapshot_count != len(history):
            errors.append("summary.snapshot_count must equal len(history)")
        if max_snapshots < 1:
            errors.append("summary.max_snapshots must be >= 1")
        if max_snapshots and snapshot_count > max_snapshots:
            errors.append("summary.snapshot_count must be <= max_snapshots")
        if not summary.get("latest_generated_at"):
            errors.append("summary.latest_generated_at is required")

        latest = history[-1] if history else {}
        if not isinstance(latest, dict):
            errors.append("latest history row must be an object")
            latest = {}

        for key in REQUIRED_LATEST_KEYS:
            if key not in latest:
                errors.append(f"latest history missing key: {key}")

        total_bets = as_int(latest.get("total_bets"))
        hit_count = as_int(latest.get("hit_count"))
        miss_count = as_int(latest.get("miss_count"))
        hit_rate = as_float(latest.get("hit_rate"))
        total_stake = as_int(latest.get("total_stake_yen"))
        total_return = as_int(latest.get("total_return_yen"))
        total_profit = as_int(latest.get("total_profit_yen"))
        return_rate = as_float(latest.get("return_rate"))

        if total_bets < 1:
            errors.append("latest.total_bets must be >= 1")
        if total_bets != hit_count + miss_count:
            errors.append("latest.total_bets must equal hit_count + miss_count")
        if total_stake < 1:
            errors.append("latest.total_stake_yen must be >= 1")
        if total_return < 0:
            errors.append("latest.total_return_yen must be >= 0")
        if total_profit != total_return - total_stake:
            errors.append("latest.total_profit_yen must equal total_return_yen - total_stake_yen")

        expected_hit_rate = round(hit_count / total_bets, 4) if total_bets else 0.0
        expected_return_rate = round(total_return / total_stake, 4) if total_stake else 0.0
        if not approx_equal(hit_rate, expected_hit_rate):
            errors.append(f"latest.hit_rate mismatch: expected {expected_hit_rate}, got {hit_rate}")
        if not approx_equal(return_rate, expected_return_rate):
            errors.append(f"latest.return_rate mismatch: expected {expected_return_rate}, got {return_rate}")

        print("dashboard trend history:")
        print("  snapshot_count:", snapshot_count)
        print("  latest_snapshot_id:", latest.get("snapshot_id"))
        print("  latest_total_bets:", total_bets)
        print("  latest_hit_rate:", hit_rate)
        print("  latest_return_rate:", return_rate)
    elif data is not None:
        errors.append("JSON root must be an object")

    if errors:
        print("Validation errors:")
        for e in errors:
            print("-", e)
        raise SystemExit(1)

    print("Dashboard bet results trend history validation: OK")
    print("STEP 143 CHECK: OK")

if __name__ == "__main__":
    main()
import json
from pathlib import Path

INDEX_PATH = Path("docs/index.html")
HISTORY_PATH = Path("docs/bet_results_summary_history.json")

REQUIRED_HTML_TOKENS = [
    "STEP142_BET_RESULTS_TREND_HISTORY_STYLE",
    "STEP142_BET_RESULTS_TREND_HISTORY_HTML",
    "STEP142_BET_RESULTS_TREND_HISTORY_SCRIPT",
    "step142BetResultsTrendPanel",
    "的中判定トレンド",
    "bet_results_summary_history.json",
    "OK: 的中判定トレンドを表示しました",
]

REQUIRED_TOP_KEYS = ["generated_at", "source", "summary", "history"]
REQUIRED_SUMMARY_KEYS = ["snapshot_count", "max_snapshots", "latest_generated_at"]
REQUIRED_LATEST_KEYS = [
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

def main():
    errors = []

    if not INDEX_PATH.exists():
        errors.append(f"Missing file: {INDEX_PATH}")
    if not HISTORY_PATH.exists():
        errors.append(f"Missing file: {HISTORY_PATH}")

    if INDEX_PATH.exists():
        html = INDEX_PATH.read_text(encoding="utf-8")
        for token in REQUIRED_HTML_TOKENS:
            if token not in html:
                errors.append(f"Missing HTML token: {token}")

    data = None
    if HISTORY_PATH.exists():
        try:
            data = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append(f"Invalid JSON: {e}")

    if isinstance(data, dict):
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

        if snapshot_count < 1:
            errors.append("summary.snapshot_count must be >= 1")
        if snapshot_count != len(history):
            errors.append("summary.snapshot_count must equal len(history)")
        if max_snapshots < 1:
            errors.append("summary.max_snapshots must be >= 1")
        if max_snapshots and snapshot_count > max_snapshots:
            errors.append("summary.snapshot_count must be <= max_snapshots")
        if not summary.get("latest_generated_at"):
            errors.append("summary.latest_generated_at is required")

        latest = history[-1] if history else {}
        if not isinstance(latest, dict):
            errors.append("latest history row must be an object")
            latest = {}

        for key in REQUIRED_LATEST_KEYS:
            if key not in latest:
                errors.append(f"latest history missing key: {key}")

        total_bets = as_int(latest.get("total_bets"))
        hit_count = as_int(latest.get("hit_count"))
        miss_count = as_int(latest.get("miss_count"))
        hit_rate = as_float(latest.get("hit_rate"))
        total_stake = as_int(latest.get("total_stake_yen"))
        total_return = as_int(latest.get("total_return_yen"))
        total_profit = as_int(latest.get("total_profit_yen"))
        return_rate = as_float(latest.get("return_rate"))

        if total_bets < 1:
            errors.append("latest.total_bets must be >= 1")
        if total_bets != hit_count + miss_count:
            errors.append("latest.total_bets must equal hit_count + miss_count")
        if total_stake < 1:
            errors.append("latest.total_stake_yen must be >= 1")
        if total_return < 0:
            errors.append("latest.total_return_yen must be >= 0")
        if total_profit != total_return - total_stake:
            errors.append("latest.total_profit_yen must equal total_return_yen - total_stake_yen")

        expected_hit_rate = round(hit_count / total_bets, 4) if total_bets else 0.0
        expected_return_rate = round(total_return / total_stake, 4) if total_stake else 0.0
        if not approx_equal(hit_rate, expected_hit_rate):
            errors.append(f"latest.hit_rate mismatch: expected {expected_hit_rate}, got {hit_rate}")
        if not approx_equal(return_rate, expected_return_rate):
            errors.append(f"latest.return_rate mismatch: expected {expected_return_rate}, got {return_rate}")

        print("dashboard trend history:")
        print("  snapshot_count:", snapshot_count)
        print("  latest_snapshot_id:", latest.get("snapshot_id"))
        print("  latest_total_bets:", total_bets)
        print("  latest_hit_rate:", hit_rate)
        print("  latest_return_rate:", return_rate)
    elif data is not None:
        errors.append("JSON root must be an object")

    if errors:
        print("Validation errors:")
        for e in errors:
            print("-", e)
        raise SystemExit(1)

    print("Dashboard bet results trend history validation: OK")
    print("STEP 143 CHECK: OK")

if __name__ == "__main__":
    main()
