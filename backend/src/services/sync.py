import hashlib

from fastapi import HTTPException
from pymysql.err import IntegrityError

from src.constants.domain import ReceiptKind, SyncStatus
from src.models.db import one, rows
from src.services import ledger
from src.services.catalog import audit
from src.utils.crypto import canonical, signed

# 离线补传串行化：同一时刻只允许一个批次落账，保证按编号判重、同批原单配对与
# 等候冲销的接续不会因两个批次交错提交而各自看到“原单尚未补传”。
LOCK_NAME = 'instrument_flows:offline_sync'
LOCK_TIMEOUT = 20
ROUTE_FIELDS = ('source', 'destination', 'instrument', 'quantity')
CONTENT_FIELDS = ('reference', 'kind', 'original_reference', *ROUTE_FIELDS, 'effective_on', 'signer', 'note')

ITEM_QUERY = '''SELECT i.*, b.created_at AS batch_at, b.note AS batch_note, b.created_by AS batch_by
    FROM sync_items i JOIN sync_batches b ON b.id=i.batch_id'''

DETAILS = {
    SyncStatus.POSTED: '已入账',
    SyncStatus.PENDING_ORIGINAL: '等待原签领补传',
    SyncStatus.CONFLICT: '编号冲突，已扣住',
}


def lock(cursor):
    acquired = one(cursor, 'SELECT GET_LOCK(%s,%s) AS locked', (LOCK_NAME, LOCK_TIMEOUT))
    if not acquired or acquired['locked'] != 1:
        raise HTTPException(503, '补传队列繁忙，请稍后重试')


def content_hash(item):
    payload = {field: item.get(field) for field in CONTENT_FIELDS}
    payload['effective_on'] = str(payload['effective_on'])
    payload['quantity'] = None if payload['quantity'] is None else int(payload['quantity'])
    return hashlib.sha256(canonical(payload).encode()).hexdigest()


def _normalize(item, signer):
    return {'reference': item.reference, 'kind': str(item.kind),
            'original_reference': item.original_reference, 'source': item.source,
            'destination': item.destination, 'instrument': item.instrument, 'quantity': item.quantity,
            'effective_on': item.effective_on, 'signer': item.signer or signer, 'note': item.note}


def _same_content(item, other):
    """同号判定。补传行未声明的馆点字段（冲销常省略，沿用原单）视为一致。"""
    return (other['kind'] == item['kind']
            and (other['original_reference'] or None) == (item['original_reference'] or None)
            and str(other['effective_on']) == str(item['effective_on'])
            and other['signer'] == item['signer'] and other['note'] == item['note']
            and all(item[field] is None or other[field] == item[field] for field in ROUTE_FIELDS))


def _existing(cursor, reference):
    return one(cursor, '''SELECT r.*, o.reference AS original_reference FROM receipts r
        LEFT JOIN receipts o ON o.id=r.original_id WHERE r.reference=%s''', (reference,))


def _canonical(cursor, reference):
    """同一编号的既定内容：已入账凭据优先，否则取最早登记的补传行。"""
    receipt = _existing(cursor, reference)
    if receipt:
        return 'receipt', receipt
    item = one(cursor, 'SELECT * FROM sync_items WHERE reference=%s ORDER BY id LIMIT 1', (reference,))
    return ('item', item) if item else (None, None)


def _original_conflicted(cursor, reference):
    """该编号作为原签领时是否已被判冲突（同号异内容，旧单保留）。"""
    return bool(one(cursor, "SELECT 1 AS hit FROM sync_items WHERE kind='loan' AND reference=%s "
                            "AND status='conflict' LIMIT 1", (reference,)))


def _catalog_sets(cursor):
    return ({row['code'] for row in rows(cursor, 'SELECT code FROM halls')},
            {row['code'] for row in rows(cursor, 'SELECT code FROM instruments')},
            {row['username'] for row in rows(cursor, 'SELECT username FROM users')})


def _record(cursor, batch_id, line, item, status, detail, *, receipt_id=None):
    cursor.execute('''INSERT INTO sync_items(batch_id,line_no,reference,kind,original_reference,source,destination,
        instrument,quantity,effective_on,signer,note,content_hash,status,detail,receipt_id)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                   (batch_id, line, item['reference'], item['kind'], item['original_reference'], item['source'],
                    item['destination'], item['instrument'], item['quantity'], item['effective_on'], item['signer'],
                    item['note'], content_hash(item), status, detail, receipt_id))
    return cursor.lastrowid


def _settle(cursor, item_id, status, detail, *, receipt_id=None):
    cursor.execute('UPDATE sync_items SET status=%s,detail=%s,receipt_id=COALESCE(%s,receipt_id) WHERE id=%s',
                   (status, detail, receipt_id, item_id))


def _insert(cursor, item, *, original_id=None, route=None):
    route = route or item
    payload = {'reference': item['reference'], 'kind': item['kind'], 'original_id': original_id,
               'source': route['source'], 'destination': route['destination'], 'instrument': route['instrument'],
               'quantity': route['quantity'], 'effective_on': item['effective_on'], 'signer': item['signer'],
               'note': item['note']}
    ledger.insert(cursor, payload)
    return cursor.lastrowid


def _result(line, item, status, detail, receipt_id, item_id):
    return {'line': line, 'reference': item['reference'], 'kind': item['kind'], 'status': status,
            'detail': detail, 'receipt_id': receipt_id, 'item_id': item_id}


def _repeat(cursor, batch_id, line, item, prior_kind, prior):
    """同号同内容重跑：只登记事实，不重复写凭据，延续既定状态。"""
    if prior_kind == 'receipt':
        status, detail, receipt_id = SyncStatus.POSTED, '编号已入账且内容一致，未重复入账', prior['id']
    else:
        status, receipt_id = prior['status'], prior['receipt_id']
        detail = f'重复补传，{DETAILS[status]}'
    item_id = _record(cursor, batch_id, line, item, status, detail, receipt_id=receipt_id)
    return _result(line, item, status, detail, receipt_id, item_id)


def _conflict(cursor, batch_id, line, item, detail, *, receipt_id=None):
    item_id = _record(cursor, batch_id, line, item, SyncStatus.CONFLICT, detail, receipt_id=receipt_id)
    return _result(line, item, SyncStatus.CONFLICT, detail, receipt_id, item_id)


def _post_loan(cursor, batch_id, line, item, user, catalog):
    halls, instruments, users = catalog
    if item['signer'] not in users:
        return _conflict(cursor, batch_id, line, item, '签领账号不在名录中，已扣住')
    if item['source'] not in halls or item['destination'] not in halls:
        return _conflict(cursor, batch_id, line, item, '出借馆或入借馆不在名录中，已扣住')
    if item['instrument'] not in instruments:
        return _conflict(cursor, batch_id, line, item, '器材族不在名录中，已扣住')
    if item['source'] == item['destination']:
        return _conflict(cursor, batch_id, line, item, '出借馆与入借馆须不同，已扣住')
    item_id = _record(cursor, batch_id, line, item, SyncStatus.POSTED, '待入账')
    try:
        receipt_id = _insert(cursor, item)
    except IntegrityError as exc:
        # 单条语句失败只回滚该行，同批其余凭据继续。1062 为同号；其余视为约束不一致。
        existing = _existing(cursor, item['reference']) if exc.args[0] == 1062 else None
        if existing and _same_content(item, existing):
            detail = '编号已入账且内容一致，未重复入账'
            _settle(cursor, item_id, SyncStatus.POSTED, detail, receipt_id=existing['id'])
            return _result(line, item, SyncStatus.POSTED, detail, existing['id'], item_id)
        detail = '同号凭据已入账但内容不同，保留旧单' if existing else '凭据不满足台账约束，已扣住'
        _settle(cursor, item_id, SyncStatus.CONFLICT, detail)
        return _result(line, item, SyncStatus.CONFLICT, detail, None, item_id)
    _settle(cursor, item_id, SyncStatus.POSTED, DETAILS[SyncStatus.POSTED], receipt_id=receipt_id)
    audit(cursor, user['username'], 'loan_synced', f'{item["reference"]}@batch:{batch_id}')
    return _result(line, item, SyncStatus.POSTED, DETAILS[SyncStatus.POSTED], receipt_id, item_id)


def _attach(cursor, item_id, item, original, user):
    """把一条等候中的冲销接到原签领上，或判定冲突扣住。返回 (status, detail, receipt_id)。"""
    if not original or original['kind'] != ReceiptKind.LOAN:
        outcome = (SyncStatus.CONFLICT, '原签领编号不是有效签领单，已扣住', None)
    elif not signed(original):
        outcome = (SyncStatus.CONFLICT, '原签领签名失效，无法冲销，已扣住', None)
    elif item['effective_on'] < original['effective_on']:
        outcome = (SyncStatus.CONFLICT, '冲销生效日早于原签领，已扣住', None)
    elif any(item[field] is not None and item[field] != original[field] for field in ROUTE_FIELDS):
        outcome = (SyncStatus.CONFLICT, '冲销登记字段与原签领不一致，已扣住', None)
    elif one(cursor, 'SELECT id FROM receipts WHERE original_id=%s', (original['id'],)):
        outcome = (SyncStatus.CONFLICT, '原签领已全额冲销，已扣住', None)
    else:
        try:
            receipt_id = _insert(cursor, item, original_id=original['id'], route=original)
        except IntegrityError as exc:
            detail = ('同号凭据已入账但内容不同，保留旧单' if exc.args[0] == 1062
                      else '凭据不满足台账约束，已扣住')
            outcome = (SyncStatus.CONFLICT, detail, None)
        else:
            outcome = (SyncStatus.POSTED, '已接上原签领入账', receipt_id)
            audit(cursor, user['username'], 'reversal_synced', item['reference'])
    status, detail, receipt_id = outcome
    _settle(cursor, item_id, status, detail, receipt_id=receipt_id)
    return outcome


def _settle_group(cursor, group, status, detail, *, receipt_id=None):
    for row in group:
        _settle(cursor, row['id'], status, detail, receipt_id=receipt_id)


def _reconcile_original(cursor, original_reference, user):
    """处理引用某原签领编号的全部等候冲销，返回是否有状态变化。"""
    waiting = rows(cursor, "SELECT * FROM sync_items WHERE kind='reversal' AND status='pending_original' "
                           "AND original_reference=%s ORDER BY id", (original_reference,))
    if not waiting:
        return False
    if _original_conflicted(cursor, original_reference):
        _settle_group(cursor, waiting, SyncStatus.CONFLICT, '原签领编号冲突，关联冲销已扣住')
        return True
    original = _existing(cursor, original_reference)
    if not original:
        # 原单尚未补传，静候下一批。
        return False
    groups = {}
    for row in waiting:
        groups.setdefault(row['reference'], []).append(row)
    for reference, group in groups.items():
        receipt = _existing(cursor, reference)
        if receipt:
            if _same_content(group[0], receipt):
                _settle_group(cursor, group, SyncStatus.POSTED, '重复补传，编号已入账且内容一致',
                              receipt_id=receipt['id'])
            else:
                _settle_group(cursor, group, SyncStatus.CONFLICT, '同号凭据已入账但内容不同，保留旧单',
                              receipt_id=receipt['id'])
            continue
        status, detail, receipt_id = _attach(cursor, group[0]['id'], group[0], original, user)
        for duplicate in group[1:]:
            _settle(cursor, duplicate['id'], status, f'重复补传，{detail}', receipt_id=receipt_id)
    return True


def reconcile(cursor, user):
    """原单补到后自动接上所有等候冲销；每次推进都会让若干行离开等候态，直至稳定。"""
    while True:
        references = [row['original_reference'] for row in rows(
            cursor, "SELECT DISTINCT original_reference FROM sync_items "
                    "WHERE kind='reversal' AND status='pending_original'")]
        if not any(_reconcile_original(cursor, reference, user) for reference in references):
            return


def _submit_item(cursor, batch_id, line, item, user, catalog):
    prior_kind, prior = _canonical(cursor, item['reference'])
    if prior_kind and _same_content(item, prior):
        return _repeat(cursor, batch_id, line, item, prior_kind, prior)
    if prior_kind:
        receipt_id = prior['id'] if prior_kind == 'receipt' else prior['receipt_id']
        return _conflict(cursor, batch_id, line, item, '同号凭据已存在但内容不同，保留旧单', receipt_id=receipt_id)
    if item['signer'] not in catalog[2]:
        return _conflict(cursor, batch_id, line, item, '签领账号不在名录中，已扣住')
    if item['kind'] == ReceiptKind.LOAN:
        return _post_loan(cursor, batch_id, line, item, user, catalog)
    item_id = _record(cursor, batch_id, line, item, SyncStatus.PENDING_ORIGINAL, DETAILS[SyncStatus.PENDING_ORIGINAL])
    return _result(line, item, SyncStatus.PENDING_ORIGINAL, DETAILS[SyncStatus.PENDING_ORIGINAL], None, item_id)


def submit_batch(cursor, data, user):
    lock(cursor)
    cursor.execute('INSERT INTO sync_batches(note,created_by) VALUES (%s,%s)', (data.note, user['username']))
    batch_id = cursor.lastrowid
    audit(cursor, user['username'], 'sync_batch_received', batch_id)
    catalog = _catalog_sets(cursor)
    prepared = [(line, _normalize(item, user['username'])) for line, item in enumerate(data.items, 1)]
    # 签领先行：同批里原单即使排在冲销之后，也能在处理冲销时直接配对。
    ordered = sorted(prepared, key=lambda pair: pair[1]['kind'] != ReceiptKind.LOAN)
    for line, item in ordered:
        _submit_item(cursor, batch_id, line, item, user, catalog)
    reconcile(cursor, user)
    # 重读：本批冲销可能在 reconcile 中由“等原单”转为已入账或冲突。
    return get_batch(cursor, batch_id)


def _summary_query(where=''):
    return f'''SELECT b.*, COUNT(i.id) AS total,
        COALESCE(SUM(i.status='posted'),0) AS posted,
        COALESCE(SUM(i.status='pending_original'),0) AS pending_original,
        COALESCE(SUM(i.status='conflict'),0) AS conflict
        FROM sync_batches b LEFT JOIN sync_items i ON i.batch_id=b.id {where} GROUP BY b.id'''


def list_batches(cursor):
    return rows(cursor, _summary_query() + ' ORDER BY b.id DESC LIMIT 50')


def get_batch(cursor, batch_id):
    batch = one(cursor, _summary_query('WHERE b.id=%s'), (batch_id,))
    if not batch:
        raise HTTPException(404, '补传批次不存在')
    # 批次详情逐条列出本批登记的行（含重跑重复行），便于核对本批做了什么。
    batch['items'] = list_items(cursor, batch_id=batch_id, latest=False)
    return batch


def list_items(cursor, *, batch_id=None, reference=None, status=None, latest=True, limit=300):
    """补传明细。

    latest=True 时每张凭据只返回最新一次登记，页面据此显示“当前状态”；
    历史重跑记录仍留在库中供核对，latest=False 可逐条查看。
    """
    clauses, params = [], []
    if batch_id is not None:
        clauses.append('i.batch_id=%s')
        params.append(batch_id)
    if reference:
        clauses.append('i.reference LIKE %s')
        params.append(f'%{reference}%')
    if status:
        clauses.append('i.status=%s')
        params.append(status)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ''
    params.append(int(limit))
    if latest:
        query = (f'''SELECT i.*, b.created_at AS batch_at, b.note AS batch_note, b.created_by AS batch_by
            FROM sync_items i JOIN sync_batches b ON b.id=i.batch_id
            JOIN (SELECT reference, MAX(id) AS id FROM sync_items GROUP BY reference) last ON last.id=i.id
            {where}
            ORDER BY i.id DESC LIMIT %s''')
    else:
        query = f'{ITEM_QUERY} {where} ORDER BY i.id DESC LIMIT %s'
    return rows(cursor, query, params)


def summary(cursor):
    """按凭据去重后的当前状态计数；批次总数取全部批次。"""
    current = one(cursor, '''SELECT COUNT(*) AS total,
        COALESCE(SUM(i.status='posted'),0) AS posted,
        COALESCE(SUM(i.status='pending_original'),0) AS pending_original,
        COALESCE(SUM(i.status='conflict'),0) AS conflict
        FROM sync_items i JOIN (SELECT reference, MAX(id) AS id FROM sync_items GROUP BY reference) last
        ON last.id=i.id''')
    current['batches'] = one(cursor, 'SELECT COUNT(*) AS count FROM sync_batches')['count']
    return current
