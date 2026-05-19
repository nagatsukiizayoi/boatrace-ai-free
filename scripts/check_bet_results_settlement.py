import sqlite3
from pathlib import Path

DB_PATH = Path('db/boatrace.sqlite3')

def main():
    if not DB_PATH.exists():
        raise SystemExit('Missing database: db/boatrace.sqlite3')
    conn = sqlite3.connect(DB_PATH)
    try:
        errors = []
        table = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bet_results'").fetchone()
        if table is None:
            raise SystemExit('Missing table: bet_results')

        count = conn.execute('SELECT COUNT(*) FROM bet_results').fetchone()[0]
        hit_count = conn.execute('SELECT COUNT(*) FROM bet_results WHERE is_hit=1').fetchone()[0]
        stake_sum = conn.execute('SELECT COALESCE(SUM(stake_yen),0) FROM bet_results').fetchone()[0]
        return_sum = conn.execute('SELECT COALESCE(SUM(return_yen),0) FROM bet_results').fetchone()[0]
        profit_sum = conn.execute('SELECT COALESCE(SUM(profit_yen),0) FROM bet_results').fetchone()[0]

        print('bet_results count:', count)
        print('hit_count:', hit_count)
        print('stake_sum:', stake_sum)
        print('return_sum:', return_sum)
        print('profit_sum:', profit_sum)

        if count < 1:
            errors.append('bet_results count must be >= 1')
        if stake_sum < count * 100:
            errors.append('stake_sum looks too small')

        bad_math = conn.execute('SELECT COUNT(*) FROM bet_results WHERE profit_yen != return_yen - stake_yen').fetchone()[0]
        if bad_math:
            errors.append('profit_yen math mismatch count: ' + str(bad_math))

        invalid_hit = conn.execute('SELECT COUNT(*) FROM bet_results WHERE is_hit NOT IN (0,1)').fetchone()[0]
        if invalid_hit:
            errors.append('invalid is_hit count: ' + str(invalid_hit))

        fk_errors = conn.execute('PRAGMA foreign_key_check').fetchall()
        if fk_errors:
            errors.append('Foreign key check failed: ' + str(fk_errors))

        sample = conn.execute('SELECT race_id, bet_type, ticket, is_hit, payout_yen, return_yen, profit_yen, return_rate FROM bet_results ORDER BY race_id, bet_type, ticket LIMIT 10').fetchall()
        print('sample bet_results:', sample)

        if errors:
            print('Validation errors:')
            for e in errors:
                print('-', e)
            raise SystemExit(1)

        print('Bet results settlement validation: OK')
        print('STEP 125 SETTLEMENT CHECK: OK')
    finally:
        conn.close()

if __name__ == '__main__':
    main()
