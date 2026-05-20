import json
from pathlib import Path

JSON_PATH = Path("docs/bet_results_summary.json")

def approx_equal(a, b, tolerance=0.0001):
    return abs(float(a) - float(b)) <= tolerance

def as_int(value):
    return int(value or 0)

def as_float(value):
    return float(value or 0)

def main():
    errors = []

    if not JSON_PATH.exists():
        raise SystemExit(f"Missing file: {JSON_PATH}")

    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("JSON root must be an object")

    summary = data.get("summary") or {}
    by_type = data.get("by_bet_type") or []
    recent = data.get("recent_results") or []

    if not isinstance(summary, dict):
        errors.append("summary must be an object")
        summary = {}
    if not isinstance(by_type, list):
        errors.append("by_bet_type must be a list")
        by_type = []
    if not isinstance(recent, list):
        errors.append("recent_results must be a list")
        recent = []

    total_bets = as_int(summary.get("total_bets"))
    hit_count = as_int(summary.get("hit_count"))
    miss_count = as_int(summary.get("miss_count"))
    hit_rate = as_float(summary.get("hit_rate"))
    total_stake = as_int(summary.get("total_stake_yen"))
    total_return = as_int(summary.get("total_return_yen"))
    total_profit = as_int(summary.get("total_profit_yen"))
    return_rate = as_float(summary.get("return_rate"))
    latest_settled_at = summary.get("latest_settled_at")

    if total_bets < 1:
        errors.append("summary.total_bets must be >= 1")
    if total_stake < 1:
        errors.append("summary.total_stake_yen must be >= 1")
    if hit_count < 0 or miss_count < 0:
        errors.append("hit_count and miss_count must be >= 0")
    if total_return < 0:
        errors.append("summary.total_return_yen must be >= 0")
    if total_profit != total_return - total_stake:
        errors.append("summary.total_profit_yen must equal total_return_yen - total_stake_yen")
    if total_bets != hit_count + miss_count:
        errors.append("summary.total_bets must equal hit_count + miss_count")
    expected_hit_rate = round(hit_count / total_bets, 4) if total_bets else 0.0
    expected_return_rate = round(total_return / total_stake, 4) if total_stake else 0.0
    if not approx_equal(hit_rate, expected_hit_rate):
        errors.append(f"summary.hit_rate mismatch: expected {expected_hit_rate}, got {hit_rate}")
    if not approx_equal(return_rate, expected_return_rate):
        errors.append(f"summary.return_rate mismatch: expected {expected_return_rate}, got {return_rate}")
    if not latest_settled_at:
        errors.append("summary.latest_settled_at is required")

    if not by_type:
        errors.append("by_bet_type must not be empty")
    else:
        sum_bets = sum(as_int(x.get("total_bets")) for x in by_type if isinstance(x, dict))
        sum_hits = sum(as_int(x.get("hit_count")) for x in by_type if isinstance(x, dict))
        sum_stake = sum(as_int(x.get("total_stake_yen")) for x in by_type if isinstance(x, dict))
        sum_return = sum(as_int(x.get("total_return_yen")) for x in by_type if isinstance(x, dict))
        sum_profit = sum(as_int(x.get("total_profit_yen")) for x in by_type if isinstance(x, dict))
        if sum_bets != total_bets:
            errors.append(f"by_bet_type total_bets sum mismatch: expected {total_bets}, got {sum_bets}")
        if sum_hits != hit_count:
            errors.append(f"by_bet_type hit_count sum mismatch: expected {hit_count}, got {sum_hits}")
        if sum_stake != total_stake:
            errors.append(f"by_bet_type stake sum mismatch: expected {total_stake}, got {sum_stake}")
        if sum_return != total_return:
            errors.append(f"by_bet_type return sum mismatch: expected {total_return}, got {sum_return}")
        if sum_profit != total_profit:
            errors.append(f"by_bet_type profit sum mismatch: expected {total_profit}, got {sum_profit}")

    if not recent:
        errors.append("recent_results must not be empty")
    if len(recent) > 10:
        errors.append("recent_results must contain at most 10 rows")

    for i, row in enumerate(recent):
        if not isinstance(row, dict):
            errors.append(f"recent_results[{i}] must be an object")
            continue
        for key in ["prediction_ticket_id", "race_id", "bet_type", "ticket", "stake_yen", "is_hit", "return_yen", "profit_yen", "return_rate", "settled_at"]:
            if key not in row:
                errors.append(f"recent_results[{i}] missing key: {key}")
        if as_int(row.get("stake_yen")) < 0:
            errors.append(f"recent_results[{i}].stake_yen must be >= 0")
        if as_int(row.get("return_yen")) < 0:
            errors.append(f"recent_results[{i}].return_yen must be >= 0")

    print("bet_results summary quality:")
    print("  total_bets:", total_bets)
    print("  hit_count:", hit_count)
    print("  miss_count:", miss_count)
    print("  hit_rate:", hit_rate)
    print("  total_stake_yen:", total_stake)
    print("  total_return_yen:", total_return)
    print("  total_profit_yen:", total_profit)
    print("  return_rate:", return_rate)

    if errors:
        print("Validation errors:")
        for e in errors:
            print("-", e)
        raise SystemExit(1)

    print("Bet results summary quality validation: OK")
    print("STEP 135 CHECK: OK")

if __name__ == "__main__":
    main()
