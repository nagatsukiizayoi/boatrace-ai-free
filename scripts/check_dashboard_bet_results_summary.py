import json
from pathlib import Path

INDEX_PATH = Path("docs/index.html")
JSON_PATH = Path("docs/bet_results_summary.json")

REQUIRED_HTML_TOKENS = [
    "STEP129_BET_RESULTS_SUMMARY_STYLE",
    "STEP129_BET_RESULTS_SUMMARY_HTML",
    "STEP129_BET_RESULTS_SUMMARY_SCRIPT",
    "step129BetResultsSummaryPanel",
    "的中判定サマリー",
    "bet_results_summary.json",
    "OK: 的中判定サマリーを表示しました",
]

REQUIRED_TOP_LEVEL_KEYS = [
    "generated_at",
    "source",
    "summary",
    "by_bet_type",
    "recent_results",
]

REQUIRED_SUMMARY_KEYS = [
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

def main():
    errors = []

    if not INDEX_PATH.exists():
        errors.append(f"Missing file: {INDEX_PATH}")
    if not JSON_PATH.exists():
        errors.append(f"Missing file: {JSON_PATH}")

    html = ""
    if INDEX_PATH.exists():
        html = INDEX_PATH.read_text(encoding="utf-8")
        for token in REQUIRED_HTML_TOKENS:
            if token not in html:
                errors.append(f"Missing HTML token: {token}")

    data = None
    if JSON_PATH.exists():
        try:
            data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append(f"Invalid JSON: {e}")

    if isinstance(data, dict):
        for key in REQUIRED_TOP_LEVEL_KEYS:
            if key not in data:
                errors.append(f"Missing top-level key: {key}")

        summary = data.get("summary")
        if not isinstance(summary, dict):
            errors.append("summary must be an object")
            summary = {}

        for key in REQUIRED_SUMMARY_KEYS:
            if key not in summary:
                errors.append(f"Missing summary key: {key}")

        total_bets = int(summary.get("total_bets") or 0)
        hit_count = int(summary.get("hit_count") or 0)
        total_stake = int(summary.get("total_stake_yen") or 0)
        total_return = int(summary.get("total_return_yen") or 0)
        return_rate = float(summary.get("return_rate") or 0)

        if total_bets < 1:
            errors.append("summary.total_bets must be >= 1")
        if total_stake < 1:
            errors.append("summary.total_stake_yen must be >= 1")
        if hit_count < 0:
            errors.append("summary.hit_count must be >= 0")
        if total_return < 0:
            errors.append("summary.total_return_yen must be >= 0")
        if return_rate < 0:
            errors.append("summary.return_rate must be >= 0")

        by_type = data.get("by_bet_type")
        recent = data.get("recent_results")
        if not isinstance(by_type, list):
            errors.append("by_bet_type must be a list")
        if not isinstance(recent, list):
            errors.append("recent_results must be a list")

        print("bet_results dashboard summary:")
        print("  total_bets:", total_bets)
        print("  hit_count:", hit_count)
        print("  total_stake_yen:", total_stake)
        print("  total_return_yen:", total_return)
        print("  return_rate:", return_rate)
    elif data is not None:
        errors.append("JSON root must be an object")

    if errors:
        print("Validation errors:")
        for e in errors:
            print("-", e)
        raise SystemExit(1)

    print("Dashboard bet results summary validation: OK")
    print("STEP 130 CHECK: OK")

if __name__ == "__main__":
    main()
