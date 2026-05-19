import json
from pathlib import Path

HEALTHCHECK_PATH = Path('docs/healthcheck.html')
SUMMARY_PATH = Path('docs/prediction_run_summary.json')

REQUIRED_HTML_TOKENS = [
    'STEP116_PREDICTION_RUN_HEALTHCHECK_STYLE',
    'STEP116_PREDICTION_RUN_HEALTHCHECK_HTML',
    'STEP116_PREDICTION_RUN_HEALTHCHECK_SCRIPT',
    'step116PredictionRunHealthPanel',
    '予測実行履歴 Health Check',
    'prediction_run_summary.json',
]

ALLOWED_STATUSES = {'created', 'running', 'completed', 'failed', 'cancelled'}

def as_int(value):
    try:
        return int(value)
    except Exception:
        return 0

def main():
    errors = []

    if not HEALTHCHECK_PATH.exists():
        raise SystemExit('Missing docs/healthcheck.html')
    if not SUMMARY_PATH.exists():
        raise SystemExit('Missing docs/prediction_run_summary.json')

    html = HEALTHCHECK_PATH.read_text(encoding='utf-8')
    for token in REQUIRED_HTML_TOKENS:
        if token not in html:
            errors.append('Missing HTML token: ' + token)

    data = json.loads(SUMMARY_PATH.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        errors.append('prediction_run_summary.json must be object')
        data = {}

    for key in ['generated_at', 'source', 'latest', 'runs', 'summary']:
        if key not in data:
            errors.append('Missing top-level key: ' + key)

    latest = data.get('latest') or {}
    runs = data.get('runs') or []
    summary = data.get('summary') or {}

    if not isinstance(latest, dict):
        errors.append('latest must be object')
        latest = {}
    if not isinstance(runs, list) or not runs:
        errors.append('runs must be non-empty list')
    if not isinstance(summary, dict):
        errors.append('summary must be object')
        summary = {}

    required_latest = ['run_key', 'model_name', 'model_version', 'target_date', 'status', 'race_count', 'recommendation_count', 'high_ev_count', 'alert_count', 'quality_score']
    for key in required_latest:
        if key not in latest:
            errors.append('Missing latest key: ' + key)

    status = latest.get('status')
    if status not in ALLOWED_STATUSES:
        errors.append('Invalid latest.status: ' + str(status))
    if status != 'completed':
        errors.append('latest.status should be completed')

    if as_int(latest.get('race_count')) < 1:
        errors.append('latest.race_count must be >= 1')
    if as_int(latest.get('recommendation_count')) < 1:
        errors.append('latest.recommendation_count must be >= 1')
    if as_int(latest.get('high_ev_count')) < 1:
        errors.append('latest.high_ev_count must be >= 1')

    print('latest run_key:', latest.get('run_key'))
    print('latest status:', latest.get('status'))
    print('run_count:', summary.get('run_count', len(runs) if isinstance(runs, list) else 0))
    print('quality_score:', latest.get('quality_score'))

    if errors:
        print('Validation errors:')
        for e in errors:
            print('-', e)
        raise SystemExit(1)

    print('Healthcheck prediction run summary validation: OK')
    print('STEP 117 CHECK: OK')

if __name__ == '__main__':
    main()
