import json

from scripts.fixtures import HALLS, INSTRUMENTS, LOANS, REVERSALS, SERIES, USERS
from src.models.db import one, transaction
from src.services.ledger import insert
from src.services.pivot import calculate
from src.services.plans import snapshot_for
from src.services.reports import save_report
from src.utils.crypto import canonical, hash_password


def seed(cursor):
    for username, name, role, password in USERS:
        cursor.execute('''INSERT INTO users(username,display_name,role,password_hash) VALUES (%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE username=username''', (username, name, role, hash_password(password)))
    cursor.executemany('INSERT INTO halls VALUES (%s,%s,%s,%s) ON DUPLICATE KEY UPDATE code=code', HALLS)
    cursor.executemany('INSERT INTO instruments VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE code=code', INSTRUMENTS)
    for reference, effective_on, source, destination, instrument, quantity, note in LOANS:
        insert(cursor, dict(reference=reference, effective_on=effective_on, source=source, destination=destination,
                            instrument=instrument, quantity=quantity, note=note, kind='loan', original_id=None,
                            signer='analyst'), seed=True)
    for reference, effective_on, original, note in REVERSALS:
        row = one(cursor, 'SELECT id,source,destination,instrument,quantity FROM receipts WHERE reference=%s', (original,))
        insert(cursor, dict(reference=reference, effective_on=effective_on, note=note, kind='reversal',
                            original_id=row.pop('id'), signer='analyst', **row), seed=True)
    cursor.execute('''INSERT INTO plans(series,version,start_on,end_on,created_by)
        VALUES (%s,1,'2026-11-02','2026-11-15','analyst') ON DUPLICATE KEY UPDATE id=id''', (SERIES,))
    if not one(cursor, "SELECT id FROM runs WHERE seed_key='november-baseline'"):
        plan = one(cursor, 'SELECT * FROM plans WHERE series=%s AND version=1', (SERIES,))
        snapshot_json = snapshot_for(cursor, plan)
        snapshot = json.loads(snapshot_json)
        result = calculate(snapshot)
        cursor.execute('''INSERT INTO runs(seed_key,plan_id,status,snapshot,result,created_by,published_at,published_by)
            VALUES ('november-baseline',%s,'done',%s,%s,'analyst','2026-11-16 10:30:00','reviewer')''',
                       (plan['id'], snapshot_json, canonical(result)))
        save_report(cursor.lastrowid, snapshot, result)
    counts = {table: one(cursor, f'SELECT COUNT(*) AS count FROM {table}')['count'] for table in
              ('users', 'halls', 'instruments', 'receipts', 'plans', 'runs', 'audit_log')}
    print(canonical(counts))


if __name__ == '__main__':
    with transaction() as cursor:
        seed(cursor)
