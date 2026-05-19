import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path('db/boatrace.sqlite3')
OUT_PATH = Path('docs/prediction_run_summary.json')

def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def main():
    if not DB_PATH.exists():
        raise SystemExit('Missing database: db/boatrace.sqlite3')

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        table = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prediction_runs'").fetchone()
        if table is None:
            raise SystemExit('Missing table: prediction_runs')

        rows = conn.execute("""
            SELECT
                run_key,
                model_name,
                model_version,
                target_date,
                started_at,
                finished_at,
                status,
                race_count,
                recommendation_count,
                high_ev_count,
                alert_count,
                quality_score,
                created_at
            FROM prediction_runs
            ORDER BY id DESC
            LIMIT 10
        """).fetchall()

        runs = [dict(row) for row in rows]
        if not runs:
            raise SystemExit('No prediction_runs rows found')

        latest = runs[0]
        errors = []
        if not latest.get('run_key'):
            errors.append('latest.run_key is empty')
        if latest.get('status') not in {'created', 'running', 'completed', 'failed', 'cancelled'}:
            errors.append('latest.status is invalid')
        if int(latest.get('race_count') or 0) < 1:
            errors.append('latest.race_count must be >= 1')
        if int(latest.get('recommendation_count') or 0) < 1:
            errors.append('latest.recommendation_count must be >= 1')

        data = {
            'generated_at': now_iso(),
            'source': 'prediction_runs',
            'latest': latest,
            'runs': runs,
            'summary': {
                'run_count': len(runs),
                'latest_status': latest.get('status'),
                'latest_quality_score': latest.get('quality_score'),
                'latest_recommendation_count': latest.get('recommendation_count'),
                'latest_high_ev_count': latest.get('high_ev_count'),
            },
        }

        if errors:
            print('Validation errors:')
            for e in errors:
                print('-', e)
            raise SystemExit(1)

        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

        print('exported:', OUT_PATH)
        print('latest run_key:', latest.get('run_key'))
        print('latest status:', latest.get('status'))
        print('latest quality_score:', latest.get('quality_score'))
        print('STEP 113 CHECK: OK')
    finally:
        conn.close()

if __name__ == '__main__':
    main()
