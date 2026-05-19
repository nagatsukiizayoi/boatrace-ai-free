import sqlite3
from pathlib import Path

DB_PATH = Path('db/boatrace.sqlite3')
RACE_RESULTS_CSV = Path('data/import/race_results.csv')
PAYOUTS_CSV = Path('data/import/payouts.csv')

def main():
    errors = []

    if not DB_PATH.exists():
        errors.append('Missing database: db/boatrace.sqlite3')
    if not RACE_RESULTS_CSV.exists():
        errors.append('Missing CSV: data/import/race_results.csv')
    if not PAYOUTS_CSV.exists():
        errors.append('Missing CSV: data/import/payouts.csv')

    if errors:
        for e in errors:
            print('-', e)
        raise SystemExit(1)

    conn = sqlite3.connect(DB_PATH)
    try:
        for table in ['race_results', 'payouts']:
            row = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
            if row is None:
                errors.append('Missing table: ' + table)

        if not errors:
            race_result_count = conn.execute('SELECT COUNT(*) FROM race_results').fetchone()[0]
            payout_count = conn.execute('SELECT COUNT(*) FROM payouts').fetchone()[0]
            official_count = conn.execute("SELECT COUNT(*) FROM race_results WHERE result_status='official'").fetchone()[0]
            trifecta_count = conn.execute("SELECT COUNT(*) FROM payouts WHERE bet_type='trifecta'").fetchone()[0]
            exacta_count = conn.execute("SELECT COUNT(*) FROM payouts WHERE bet_type='exacta'").fetchone()[0]
            quinella_count = conn.execute("SELECT COUNT(*) FROM payouts WHERE bet_type='quinella'").fetchone()[0]

            print('race_results count:', race_result_count)
            print('payouts count:', payout_count)
            print('official results:', official_count)
            print('trifecta payouts:', trifecta_count)
            print('exacta payouts:', exacta_count)
            print('quinella payouts:', quinella_count)

            if race_result_count < 2:
                errors.append('race_results count must be >= 2')
            if payout_count < 6:
                errors.append('payouts count must be >= 6')
            if official_count < 2:
                errors.append('official race_results count must be >= 2')
            if trifecta_count < 2:
                errors.append('trifecta payout count must be >= 2')
            if exacta_count < 2:
                errors.append('exacta payout count must be >= 2')
            if quinella_count < 2:
                errors.append('quinella payout count must be >= 2')

            sample_results = conn.execute('SELECT race_id, result_status FROM race_results ORDER BY race_id LIMIT 5').fetchall()
            sample_payouts = conn.execute('SELECT race_id, bet_type, ticket, payout_yen FROM payouts ORDER BY race_id, bet_type LIMIT 10').fetchall()
            print('sample race_results:', sample_results)
            print('sample payouts:', sample_payouts)

        fk_errors = conn.execute('PRAGMA foreign_key_check').fetchall()
        if fk_errors:
            errors.append('Foreign key check failed: ' + str(fk_errors))

        if errors:
            print('Validation errors:')
            for e in errors:
                print('-', e)
            raise SystemExit(1)

        print('Results CSV import validation: OK')
        print('STEP 122 CHECK: OK')
    finally:
        conn.close()

if __name__ == '__main__':
    main()
