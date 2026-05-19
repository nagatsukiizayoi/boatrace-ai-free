import sqlite3
from pathlib import Path

DB_PATH = Path('db/boatrace.sqlite3')

RACE_RESULTS_REQUIRED = {
    'id',
    'race_id',
    'result_status',
    'created_at',
}

PAYOUTS_REQUIRED = {
    'id',
    'race_id',
    'bet_type',
    'ticket',
    'payout_yen',
    'popularity',
    'created_at',
}

RACE_RESULTS_ALIASES = {
    'first_place': {'first_place', 'first_boat_no'},
    'second_place': {'second_place', 'second_boat_no'},
    'third_place': {'third_place', 'third_boat_no'},
    'winning_method': {'winning_method', 'winning_trick'},
    'decided_at': {'decided_at', 'finalized_at'},
}

def table_exists(conn, table):
    return conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None

def columns(conn, table):
    return {r[1] for r in conn.execute('PRAGMA table_info(' + table + ')').fetchall()}

def main():
    if not DB_PATH.exists():
        raise SystemExit('Missing database: db/boatrace.sqlite3')

    conn = sqlite3.connect(DB_PATH)
    try:
        errors = []

        if not table_exists(conn, 'race_results'):
            errors.append('Missing table: race_results')
            race_cols = set()
        else:
            race_cols = columns(conn, 'race_results')
            missing = sorted(RACE_RESULTS_REQUIRED - race_cols)
            if missing:
                errors.append('race_results missing base columns: ' + ', '.join(missing))
            for logical_name, candidates in RACE_RESULTS_ALIASES.items():
                if not (race_cols & candidates):
                    errors.append('race_results missing logical column ' + logical_name + ' candidates=' + ','.join(sorted(candidates)))
            print('race_results columns:', sorted(race_cols))

        if not table_exists(conn, 'payouts'):
            errors.append('Missing table: payouts')
            payout_cols = set()
        else:
            payout_cols = columns(conn, 'payouts')
            missing = sorted(PAYOUTS_REQUIRED - payout_cols)
            if missing:
                errors.append('payouts missing columns: ' + ', '.join(missing))
            print('payouts columns:', sorted(payout_cols))

        fk_errors = conn.execute('PRAGMA foreign_key_check').fetchall()
        if fk_errors:
            errors.append('Foreign key check failed: ' + str(fk_errors))

        if errors:
            print('Validation errors:')
            for e in errors:
                print('-', e)
            raise SystemExit(1)

        print('Race results and payouts schema validation: OK')
        print('STEP 120 CHECK: OK')
    finally:
        conn.close()

if __name__ == '__main__':
    main()
