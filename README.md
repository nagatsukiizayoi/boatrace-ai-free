# boatrace-ai-free
![Dashboard readiness](https://github.com/nagatsukiizayoi/boatrace-ai-free/actions/workflows/check-dashboard-final-readiness.yml/badge.svg)

![make_prediction](https://github.com/nagatsukiizayoi/boatrace-ai-free/actions/workflows/make_prediction.yml/badge.svg)
---

## Current System Status

This repository contains a boat race prediction pipeline with SQLite database integration, prediction JSON export, dashboard display, healthcheck display, and GitHub Actions validation.

### Database Build

The integrated database schema is managed in:

- `db/schema.sql`

Standard database build commands:

```bash
python scripts/init_db.py --reset
python scripts/build_database.py --reset
python scripts/build_database.py --reset --with-sample-data
```

Integrated schema validation:

```bash
python scripts/check_integrated_schema.py
```

Expected result:

```text
STEP 104 CHECK: OK
```

### Full Prediction Pipeline

The full pipeline can be executed with:

```bash
python scripts/run_full_prediction_pipeline.py
```

The pipeline performs database initialization, CSV import, prediction generation, odds and expected value enrichment, recommendation reason enrichment, prediction run recording, and summary JSON export.

Expected results include:

```text
STEP 110 CHECK: OK
STEP 111 CHECK: OK
STEP 113 CHECK: OK
STEP 115 CHECK: OK
STEP 117 CHECK: OK
STEP 101 CHECK: OK
```

### Prediction Run History

Prediction execution history is stored in the SQLite table:

- `prediction_runs`

The run history is recorded by:

```bash
python scripts/record_prediction_run.py
```

Validation:

```bash
python scripts/check_prediction_run_recording.py
```

Expected result:

```text
STEP 111 CHECK: OK
```

### Static Prediction Run Summary JSON

Because GitHub Pages cannot read SQLite directly, prediction run history is exported to:

- `docs/prediction_run_summary.json`

Export command:

```bash
python scripts/export_prediction_run_summary.py
```

Expected result:

```text
STEP 113 CHECK: OK
```

### Dashboard and Healthcheck

Dashboard:

- `docs/index.html`
- Displays prediction data, EV summaries, recommendation reasons, quality score, and prediction run summary.

Healthcheck:

- `docs/healthcheck.html`
- Displays healthcheck panels for prediction JSON, EV data, recommendation reasons, and prediction run summary.

Local dashboard checks:

```bash
python scripts/check_dashboard_final_readiness.py
python scripts/check_dashboard_prediction_run_summary.py
python scripts/check_healthcheck_prediction_run_summary.py
```

Expected results:

```text
STEP 100 CHECK: OK
STEP 115 CHECK: OK
STEP 117 CHECK: OK
```

### Main GitHub Actions Workflows

Important workflows include:

- `Check Full Prediction Pipeline`
- `Check Integrated Schema`
- `Check Prediction Run Recording`
- `Check Dashboard Prediction Run Summary`
- `Check Healthcheck Prediction Run Summary`
- `Check Dashboard Final Readiness`

### GitHub Pages

Dashboard:

- `https://nagatsukiizayoi.github.io/boatrace-ai-free/`

Healthcheck:

- `https://nagatsukiizayoi.github.io/boatrace-ai-free/healthcheck.html`

Prediction JSON:

- `https://nagatsukiizayoi.github.io/boatrace-ai-free/prediction.json`

Prediction run summary JSON:

- `https://nagatsukiizayoi.github.io/boatrace-ai-free/prediction_run_summary.json`

### STEP119 Completion

STEP119 is complete when this README contains the latest database build flow, full prediction pipeline flow, prediction_runs usage, prediction_run_summary.json usage, dashboard and healthcheck references, and main GitHub Actions workflow list.

<!-- STEP134_BET_RESULTS_FLOW -->
## Bet Results / 的中判定フロー

このプロジェクトでは、予測買い目とレース結果・払戻データを照合し、的中判定と回収率を `bet_results` テーブルに保存します。

### Main flow

1. 予測データを生成する
2. レース結果CSVと払戻CSVを取り込む
3. 予測買い目と払戻を照合する
4. `bet_results` に的中判定・払戻・利益・回収率を保存する
5. `docs/bet_results_summary.json` を出力する
6. dashboard と healthcheck に的中判定サマリーを表示する

### Key database table

- `bet_results`
  - `prediction_ticket_id`
  - `race_id`
  - `bet_type`
  - `ticket`
  - `stake_yen`
  - `is_hit`
  - `payout_yen`
  - `return_yen`
  - `profit_yen`
  - `return_rate`
  - `settled_at`

### Key scripts

- `scripts/import_results_csv.py`
  - `data/import/race_results.csv` と `data/import/payouts.csv` をDBへ取り込みます。
- `scripts/settle_bet_results.py`
  - `prediction_tickets.prediction_id -> predictions.id -> predictions.race_id` を辿って race_id を解決し、払戻と照合します。
- `scripts/check_bet_results_settlement.py`
  - `bet_results` の件数、的中数、投資額、払戻額、利益、外部キー整合性を検証します。
- `scripts/export_bet_results_summary.py`
  - `docs/bet_results_summary.json` を出力します。
- `scripts/check_dashboard_bet_results_summary.py`
  - dashboard の的中判定サマリー表示を検証します。
- `scripts/check_healthcheck_bet_results_summary.py`
  - healthcheck の的中判定サマリー表示を検証します。

### Full pipeline command

```bash
python scripts/run_full_prediction_pipeline.py
```

Expected checks include:

```text
STEP 121 CHECK: OK
STEP 122 CHECK: OK
STEP 125 CHECK: OK
STEP 125 SETTLEMENT CHECK: OK
STEP 128 CHECK: OK
STEP 130 CHECK: OK
STEP 132 CHECK: OK
STEP 101 CHECK: OK
```

### Manual commands

```bash
python scripts/import_results_csv.py
python scripts/settle_bet_results.py
python scripts/check_bet_results_settlement.py
python scripts/export_bet_results_summary.py
python scripts/check_dashboard_bet_results_summary.py
python scripts/check_healthcheck_bet_results_summary.py
```

### Output JSON

- `docs/bet_results_summary.json`
  - `generated_at`
  - `source`
  - `summary`
  - `by_bet_type`
  - `recent_results`

The summary includes total bets, hit count, hit rate, total stake, total return, total profit, return rate, and latest settlement time.

### Dashboard / Healthcheck

- Dashboard:
  - `docs/index.html`
  - displays `的中判定サマリー`
- Healthcheck:
  - `docs/healthcheck.html`
  - displays `的中判定 Health Check`

GitHub Pages URLs:

- https://nagatsukiizayoi.github.io/boatrace-ai-free/
- https://nagatsukiizayoi.github.io/boatrace-ai-free/healthcheck.html

### GitHub Actions

Related workflows:

- `Check Bet Results Settlement`
- `Check Dashboard Bet Results Summary`
- `Check Healthcheck Bet Results Summary`
- `Check Full Prediction Pipeline`

<!-- STEP134_END -->

<- STEP71_MAKE_PREDICTION_WORKFLOW_DOC -->

## make_prediction workflow / prediction JSON generation

The make_prediction workflow builds the sample database, runs the full prediction pipeline, exports docs/prediction.json and docs/prediction_run_summary.json, and validates them.

### Related checks

- scripts/check_prediction_json_structure.py
- scripts/check_prediction_run_summary_structure.py
- scripts/check_prediction_outputs_consistency.py
- scripts/check_make_prediction_workflow.py
- scripts/check_make_prediction_outputs_ready.py

Expected success messages: STEP 66 CHECK: OK through STEP 70 CHECK: OK.

Workflow file: .github/workflows/make_prediction.yml

<- STEP71_END -->

<- STEP77_MAKE_PREDICTION_SCHEDULE_DOC -->

### Scheduled execution

The  workflow runs automatically on a schedule.

- Cron: 
- Timezone: UTC
- Japan time: every day around 21:00 JST
- Manual execution is also available via .

<- STEP77_END -->

<!-- STEP77_MAKE_PREDICTION_SCHEDULE_DOC -->

### Scheduled execution

The make_prediction workflow runs automatically on a schedule.

- Cron: 0 12 * * *
- Timezone: UTC
- Japan time: every day around 21:00 JST
- Manual execution is also available via workflow_dispatch.

<!-- STEP77_END -->

<!-- STEP82_DASHBOARD_READINESS_DOC -->

## Dashboard readiness and prediction JSON compatibility

The dashboard readiness checks verify that the generated dashboard files and prediction JSON are ready for GitHub Pages display.

Related files:

- `docs/index.html`
- `docs/healthcheck.html`
- `docs/prediction.json`
- `scripts/ensure_prediction_json_dashboard_compat.py`
- `scripts/check_recommendation_reasons.py`
- `scripts/check_dashboard_final_readiness.py`

The compatibility script updates `docs/prediction.json` so that dashboard-required fields are present, including:

- `expected_value`
- `value_grade`
- `reason_version`
- `recommendation_reason`
- `reason_points`
- `risk_note`
- `recommendation_reasoning.version`

Expected success messages:

- `STEP 80 CHECK: OK`
- `STEP 100 CHECK: OK`

Local verification:

`python scripts/ensure_prediction_json_dashboard_compat.py`
`python scripts/check_recommendation_reasons.py`
`python scripts/check_dashboard_final_readiness.py`

<!-- STEP82_END -->

