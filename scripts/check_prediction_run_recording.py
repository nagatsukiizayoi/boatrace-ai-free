import sqlite3
from pathlib import Path

DB_PATH = Path('db/boatrace.sqlite3')

REQUIRED_COLUMNS = {
    'id',
    'run_key',
    'model_name',
    'model_version',
    'target_date',
    'started_at',
    'finished_at',
    'status',
    'race_count',
    'recommendation_count',
    'high_ev_count',
    'alert_count',
    'quality_score',
}

ALLOWED_STATUSES = {'created', 'running', 'completed', 'failed', 'cancelled'}

def main():
    if not DB_PATH.exists():
        raise SystemExit('Missing database: db/boatrace.sqlite3')

    conn = sqlite3.connect(DB_PATH)
    try:
        table = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prediction_runs'").fetchone()
        if table is None:
            raise SystemExit('Missing table: prediction_runs')

        columns = {row[1] for row in conn.execute('PRAGMA table_info(prediction_runs)').fetchall()}
        missing_columns = sorted(REQUIRED_COLUMNS - columns)
        if missing_columns:
            raise SystemExit('Missing prediction_runs columns: ' + ', '.join(missing_columns))

        rows = conn.execute("SELECT run_key, model_name, model_version, target_date, status, race_count, recommendation_count, high_ev_count, alert_count, quality_score FROM prediction_runs ORDER BY id DESC").fetchall()
        if not rows:
            raise SystemExit('No rows in prediction_runs')

        latest = rows[0]
        run_key, model_name, model_version, target_date, status, race_count, recommendation_count, high_ev_count, alert_count, quality_score = latest

        errors = []
        if not run_key:
            errors.append('run_key is empty')
        if not model_name:
            errors.append('model_name is empty')
        if not model_version:
            errors.append('model_version is empty')
        if not target_date:
            errors.append('target_date is empty')
        if status not in ALLOWED_STATUSES:
            errors.append('invalid status: ' + str(status))
        if race_count < 1:
            errors.append('race_count must be >= 1')
        if recommendation_count < 1:
            errors.append('recommendation_count must be >= 1')
        if high_ev_count < 1:
            errors.append('high_ev_count must be >= 1')
        if quality_score is None:
            errors.append('quality_score is missing')

        print('prediction_runs rows:', len(rows))
        print('latest run:', latest)

        if errors:
            print('Validation errors:')
            for e in errors:
                print('-', e)
            raise SystemExit(1)

        print('Prediction run recording validation: OK')
        print('STEP 111 CHECK: OK')
    finally:
        conn.close()

if __name__ == '__main__':
    main()
