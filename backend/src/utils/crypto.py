import hashlib
import hmac
import json
import secrets

from src.config.settings import LEDGER_SECRET


def canonical(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), sort_keys=True, default=str)


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 210_000)
    return f'{salt}${digest.hex()}'


def check_password(password, encoded):
    return hmac.compare_digest(hash_password(password, encoded.split('$')[0]), encoded)


def receipt_signature(row):
    fields = ('reference', 'kind', 'original_id', 'source', 'destination', 'instrument',
              'quantity', 'effective_on', 'signer', 'note')
    payload = {field: row[field] for field in fields}
    payload['effective_on'] = str(payload['effective_on'])
    return hmac.new(LEDGER_SECRET, canonical(payload).encode(), hashlib.sha256).hexdigest()


def signed(row):
    return hmac.compare_digest(receipt_signature(row), row['signature'])
