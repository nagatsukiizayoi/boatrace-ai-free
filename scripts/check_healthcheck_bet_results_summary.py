import json
from pathlib import Path

HEALTHCHECK_PATH = Path("docs/healthcheck.html")
JSON_PATH = Path("docs/bet_results_summary.json")

REQUIRED_HTML_TOKENS = [
    "的中判定 Health Check",
    "bet_results_summary.json",
    "OK: 的中判定 Health Check を表示しました",
]

OPTIONAL_STEP131_TOKENS = [
    "STEP131_BET_RESULTS_HEALTHCHECK",
    "STEP131_BET_RESULTS_HEALTHCHECK_VISIBLE_FIX",
    "step131BetResultsHealthPanel",
    "step131BetResultsHealthPanelVisibleFix",
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

    if not HEALTHCHECK_PATH.exists():
        errors.append(f"Missing file: {HEALTHCHECK_PATH}")
    if not JSON_PATH.exists():
        errors.append(f"Missing file: {JSON_PATH}")

    html = ""
    if HEALTHCHECK_PATH.exists():
        html = HEALTHCHECK_PATH.read_text(encoding="utf-8")
        for token in REQUIRED_HTML_TOKENS:
            if token not in html:
                errors.append(f"Missing HTML token: {token}")
        if not any(token in html for token in OPTIONAL_STEP131_TOKENS):
            errors.append("Missing STEP131 marker or panel id")

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

        if not isinstance(data.get("by_bet_type"), list):
            errors.append("by_bet_type must be a list")
        if not isinstance(data.get("recent_results"), list):
            errors.append("recent_results must be a list")

        print("healthcheck bet_results summary:")
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

    print("Healthcheck bet results summary validation: OK")
    print("STEP 132 CHECK: OK")

if __name__ == "__main__":
    main()
