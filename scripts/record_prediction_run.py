import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path('db/boatrace.sqlite3')
JSON_PATH = Path('docs/prediction.json')

def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def to_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default

def load_data():
    if not JSON_PATH.exists():
        raise SystemExit('Missing docs/prediction.json')
    with JSON_PATH.open('r', encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise SystemExit('prediction.json must be object')
    return data

def collect_metrics(data):
    run_key = str(data.get('run_key') or '').strip()
    model_name = str(data.get('model_name') or '').strip()
    model_version = str(data.get('model_version') or '').strip()
    target_date = str(data.get('target_date') or '').strip()
    updated_at = str(data.get('updated_at') or '').strip()
    missing = [k for k, v in {'run_key': run_key, 'model_name': model_name, 'model_version': model_version, 'target_date': target_date}.items() if not v]
    if missing:
        raise SystemExit('Missing required fields: ' + ', '.join(missing))
    races = data.get('races') or []
    alerts = data.get('alerts') or []
    summary = data.get('summary') or {}
    if not isinstance(races, list):
        raise SystemExit('races must be list')
    if not isinstance(alerts, list):
        alerts = []
    if not isinstance(summary, dict):
        summary = {}

    recommendation_count = 0
    high_ev_count = 0
    for race in races:
        if not isinstance(race, dict):
            continue
        recommendations = race.get('recommendations') or []
        if not isinstance(recommendations, list):
            continue
        for rec in recommendations:
            if not isinstance(rec, dict):
                continue
            recommendation_count += 1
            if to_float(rec.get('expected_value')) >= 1.2:
                high_ev_count += 1
    quality_score = data.get('quality_score')
    if quality_score is None:
        quality_score = summary.get('quality_score')
    if quality_score is None:
        score = 0.0
        if len(races) > 0:
            score += 25.0
        if recommendation_count > 0:
            score += 25.0
        if high_ev_count > 0:
            score += 20.0
        if len(alerts) > 0:
            score += 10.0
        if data.get('recommendation_reasoning'):
            score += 20.0
        quality_score = min(score, 100.0)
    return {
        'run_key': run_key,
        'model_name': model_name,
        'model_version': model_version,
        'target_date': target_date,
        'started_at': updated_at or now_iso(),
        'finished_at': now_iso(),
        'status': 'completed',
        'race_count': len(races),
        'recommendation_count': recommendation_count,
        'high_ev_count': high_ev_count,
        'alert_count': len(alerts),
        'quality_score': to_float(quality_score),
    }

def main():
    if not DB_PATH.exists():
        raise SystemExit('Missing db/boatrace.sqlite3. Run python scripts/init_db.py --reset first.')
    data = load_data()
    metrics = collect_metrics(data)
    conn = sqlite3.connect(DB_PATH)
    try:
        table = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prediction_runs'").fetchone()
        if table is None:
            raise SystemExit('prediction_runs table does not exist')
        cols = {r[1] for r in conn.execute("PRAGMA table_info(prediction_runs)").fetchall()}
        migrations = [("started_at", "ALTER TABLE prediction_runs ADD COLUMN started_at TEXT"), ("finished_at", "ALTER TABLE prediction_runs ADD COLUMN finished_at TEXT"), ("race_count", "ALTER TABLE prediction_runs ADD COLUMN race_count INTEGER NOT NULL DEFAULT 0"), ("recommendation_count", "ALTER TABLE prediction_runs ADD COLUMN recommendation_count INTEGER NOT NULL DEFAULT 0"), ("high_ev_count", "ALTER TABLE prediction_runs ADD COLUMN high_ev_count INTEGER NOT NULL DEFAULT 0"), ("alert_count", "ALTER TABLE prediction_runs ADD COLUMN alert_count INTEGER NOT NULL DEFAULT 0"), ("quality_score", "ALTER TABLE prediction_runs ADD COLUMN quality_score REAL")]
        for name, sql in migrations:
            if name not in cols:
                conn.execute(sql)
        conn.commit()
        conn.execute("""
            INSERT INTO prediction_runs (
                run_key, model_name, model_version, target_date,
                started_at, finished_at, status, race_count,
                recommendation_count, high_ev_count, alert_count, quality_score
            ) VALUES (
                :run_key, :model_name, :model_version, :target_date,
                :started_at, :finished_at, :status, :race_count,
                :recommendation_count, :high_ev_count, :alert_count, :quality_score
            )
            ON CONFLICT(run_key) DO UPDATE SET
                model_name=excluded.model_name,
                model_version=excluded.model_version,
                target_date=excluded.target_date,
                started_at=excluded.started_at,
                finished_at=excluded.finished_at,
                status=excluded.status,
                race_count=excluded.race_count,
                recommendation_count=excluded.recommendation_count,
                high_ev_count=excluded.high_ev_count,
                alert_count=excluded.alert_count,
                quality_score=excluded.quality_score
        """, metrics)
        conn.commit()
        row = conn.execute('SELECT run_key, model_name, model_version, target_date, status, race_count, recommendation_count, high_ev_count, alert_count, quality_score FROM prediction_runs WHERE run_key=?', (metrics['run_key'],)).fetchone()
        print('Recorded prediction run:', row)
        if row is None:
            raise SystemExit('insert failed')
        if row[5] < 1 or row[6] < 1 or row[7] < 1:
            raise SystemExit('invalid counts in prediction_runs')
        print('STEP 110 CHECK: OK')
    finally:
        conn.close()

if __name__ == '__main__':
    main()
