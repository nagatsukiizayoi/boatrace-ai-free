import sqlite3
from pathlib import Path

DB_PATH = Path('db/boatrace.sqlite3')

REQUIRED_COLUMNS = {
    'id',
    'prediction_ticket_id',
    'race_id',
    'bet_type',
    'ticket',
    'stake_yen',
    'is_hit',
    'payout_yen',
    'return_yen',
    'profit_yen',
    'return_rate',
    'settled_at',
    'created_at',
    'updated_at',
}

def main():
    if not DB_PATH.exists():
        raise SystemExit('Missing database: db/boatrace.sqlite3')

    conn = sqlite3.connect(DB_PATH)
    try:
        errors = []
        row = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bet_results'").fetchone()
        if row is None:
            errors.append('Missing table: bet_results')
            cols = set()
        else:
            cols = {r[1] for r in conn.execute('PRAGMA table_info(bet_results)').fetchall()}
            missing = sorted(REQUIRED_COLUMNS - cols)
            if missing:
                errors.append('bet_results missing columns: ' + ', '.join(missing))
            print('bet_results columns:', sorted(cols))

        fk_errors = conn.execute('PRAGMA foreign_key_check').fetchall()
        if fk_errors:
            errors.append('Foreign key check failed: ' + str(fk_errors))

        if errors:
            print('Validation errors:')
            for e in errors:
                print('-', e)
            raise SystemExit(1)

        print('Bet results schema validation: OK')
        print('STEP 124 CHECK: OK')
    finally:
        conn.close()

if __name__ == '__main__':
    main()
