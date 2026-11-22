from fastapi import HTTPException

from src.constants.domain import ReceiptKind
from src.models.db import one, rows
from src.services.catalog import audit
from src.utils.crypto import receipt_signature, signed

LEDGER_QUERY = '''SELECT r.*, o.reference AS original_reference, x.reference AS reversed_by,
    u.display_name AS signer_name FROM receipts r
    LEFT JOIN receipts o ON o.id=r.original_id LEFT JOIN receipts x ON x.original_id=r.id
    JOIN users u ON u.username=r.signer'''


def ledger(cursor):
    return [{**row, 'signature_valid': signed(row)} for row in rows(
        cursor, LEDGER_QUERY + ' ORDER BY r.effective_on DESC,r.id DESC LIMIT 500')]


def insert(cursor, row, *, seed=False):
    row['signature'] = receipt_signature(row)
    sql = '''INSERT INTO receipts(reference,kind,original_id,source,destination,instrument,quantity,
        effective_on,signer,note,signature) VALUES (%(reference)s,%(kind)s,%(original_id)s,%(source)s,
        %(destination)s,%(instrument)s,%(quantity)s,%(effective_on)s,%(signer)s,%(note)s,%(signature)s)'''
    if seed:
        sql += ' ON DUPLICATE KEY UPDATE id=id'
    cursor.execute(sql, row)
    return row


def add_loan(cursor, data, user):
    if data.source == data.destination:
        raise HTTPException(422, '出借馆与入借馆须不同')
    row = insert(cursor, {**data.model_dump(), 'kind': ReceiptKind.LOAN, 'original_id': None,
                          'signer': user['username']})
    audit(cursor, user['username'], 'loan_signed', row['reference'])
    return row


def add_reversal(cursor, data, user):
    original = one(cursor, 'SELECT * FROM receipts WHERE reference=%s FOR UPDATE', (data.original_reference,))
    if not original or original['kind'] != ReceiptKind.LOAN:
        raise HTTPException(422, '冲销须引用有效的原始签领编号')
    if not signed(original):
        raise HTTPException(409, '原签领签名失效，无法冲销')
    if data.effective_on < original['effective_on']:
        raise HTTPException(422, '冲销日期不得早于原签领')
    if one(cursor, 'SELECT id FROM receipts WHERE original_id=%s FOR UPDATE', (original['id'],)):
        raise HTTPException(409, '该签领已全额冲销')
    row = insert(cursor, {**data.model_dump(exclude={'original_reference'}), 'kind': ReceiptKind.REVERSAL,
                          'original_id': original['id'], 'source': original['source'],
                          'destination': original['destination'], 'instrument': original['instrument'],
                          'quantity': original['quantity'], 'signer': user['username']})
    audit(cursor, user['username'], 'reversal_signed', row['reference'])
    return row
