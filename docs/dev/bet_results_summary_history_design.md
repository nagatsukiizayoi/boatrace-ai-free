# Bet Results Summary History Design

<!-- STEP137_BET_RESULTS_SUMMARY_HISTORY_DESIGN -->

## Overview

This document defines the design for storing historical trend snapshots of bet result summaries.

Current latest summary file:

- `docs/bet_results_summary.json`

Planned history file:

- `docs/bet_results_summary_history.json`

## Purpose

The history file will preserve trend snapshots so dashboard and healthcheck pages can show changes over time.

Tracked metrics:

- total bets
- hit count
- miss count
- hit rate
- total stake yen
- total return yen
- total profit yen
- return rate
- latest settled timestamp

## Planned JSON Structure

```json
{
  "generated_at": "2026-01-01T00:00:00+00:00",
  "source": "docs/bet_results_summary.json",
  "summary": {
    "snapshot_count": 1,
    "max_snapshots": 50,
    "latest_generated_at": "2026-01-01T00:00:00+00:00"
  },
  "history": [
    {
      "snapshot_id": "bet-results-20260101000000",
      "generated_at": "2026-01-01T00:00:00+00:00",
      "total_bets": 10,
      "hit_count": 2,
      "miss_count": 8,
      "hit_rate": 0.2,
      "total_stake_yen": 1000,
      "total_return_yen": 1200,
      "total_profit_yen": 200,
      "return_rate": 1.2,
      "latest_settled_at": "2026-01-01T00:00:00+00:00"
    }
  ]
}
```

## Update Policy

- A new snapshot is appended after `docs/bet_results_summary.json` is exported.
- Snapshots are ordered from oldest to newest.
- The maximum number of snapshots is initially 50.
- If the number of snapshots exceeds the limit, older snapshots are removed.
- Duplicate snapshots with the same `latest_settled_at` and same aggregate values should not be appended repeatedly.

## Validation Rules

- `history` must be a list.
- `snapshot_count` must equal the length of `history`.
- `total_bets` must be greater than or equal to 1.
- `total_bets` must equal `hit_count + miss_count`.
- `hit_rate` must equal `hit_count / total_bets` rounded to 4 decimals.
- `return_rate` must equal `total_return_yen / total_stake_yen` rounded to 4 decimals.
- `total_profit_yen` must equal `total_return_yen - total_stake_yen`.
- Negative values are not allowed for counts, stake, or return.

## Planned Scripts

- `scripts/export_bet_results_summary_history.py`
  - Reads `docs/bet_results_summary.json`.
  - Appends a trend snapshot to `docs/bet_results_summary_history.json`.
  - Keeps only the latest 50 snapshots.
  - Prints `STEP 138 CHECK: OK`.

- `scripts/check_bet_results_summary_history.py`
  - Validates the history JSON structure and aggregate consistency.
  - Prints `STEP 139 CHECK: OK`.

## Full Pipeline Integration Plan

After STEP138 and STEP139, the full pipeline should run:

```bash
python scripts/export_bet_results_summary.py
python scripts/check_bet_results_summary_quality.py
python scripts/export_bet_results_summary_history.py
python scripts/check_bet_results_summary_history.py
```

## Dashboard / Healthcheck Future Plan

- Dashboard can display hit rate and return rate trends.
- Healthcheck can validate that trend history is being updated.
- Future visualization can use simple tables or small trend cards.

## STEP137 Completion Criteria

- This design document exists.
- The planned history JSON structure is defined.
- Update and validation rules are documented.
- Planned scripts and future pipeline integration are documented.

STEP137: completed.
