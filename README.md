# boatrace-ai-free
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
