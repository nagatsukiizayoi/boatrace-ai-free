import csv
import sqlite3
from pathlib import Path

DB_PATH = Path('db/boatrace.sqlite3')
RACE_RESULTS_CSV = Path('data/import/race_results.csv')
PAYOUTS_CSV = Path('data/import/payouts.csv')

def table_columns(conn, table):
    return [r[1] for r in conn.execute('PRAGMA table_info(' + table + ')').fetchall()]

def read_csv(path):
    if not path.exists():
        raise SystemExit('Missing CSV: ' + str(path))
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def insert_dynamic(conn, table, rows):
    if not rows:
        return 0
    cols = table_columns(conn, table)
    insertable = [c for c in rows[0].keys() if c in cols]
    if not insertable:
        raise SystemExit('No insertable columns for ' + table)
    placeholders = ','.join(['?'] * len(insertable))
    sql = 'INSERT INTO ' + table + ' (' + ','.join(insertable) + ') VALUES (' + placeholders + ')'
    count = 0
    for row in rows:
        values = [row.get(c) for c in insertable]
        conn.execute(sql, values)
        count += 1
    return count

def main():
    if not DB_PATH.exists():
        raise SystemExit('Missing database: db/boatrace.sqlite3')
    race_rows = read_csv(RACE_RESULTS_CSV)
    payout_rows = read_csv(PAYOUTS_CSV)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute('PRAGMA foreign_keys = ON')
        race_ids = sorted({int(r['race_id']) for r in race_rows if r.get('race_id')})
        for race_id in race_ids:
            exists = conn.execute('SELECT id FROM races WHERE id=?', (race_id,)).fetchone()
            if exists is None:
                raise SystemExit('Missing races.id for race_id=' + str(race_id))
        for race_id in race_ids:
            conn.execute('DELETE FROM payouts WHERE race_id=?', (race_id,))
            conn.execute('DELETE FROM race_results WHERE race_id=?', (race_id,))
        result_count = insert_dynamic(conn, 'race_results', race_rows)
        payout_count = insert_dynamic(conn, 'payouts', payout_rows)
        conn.commit()
        print('imported race_results:', result_count)
        print('imported payouts:', payout_count)
        if result_count < 1:
            raise SystemExit('race_results import count must be >= 1')
        if payout_count < 1:
            raise SystemExit('payouts import count must be >= 1')
        fk_errors = conn.execute('PRAGMA foreign_key_check').fetchall()
        if fk_errors:
            raise SystemExit('Foreign key check failed: ' + str(fk_errors))
        print('STEP 121 CHECK: OK')
    finally:
        conn.close()

if __name__ == '__main__':
    main()
