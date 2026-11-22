import json
import logging
import time
from pathlib import Path

from src.config.settings import CACHE
from src.models.db import one, transaction
from src.services.pivot import LedgerMismatch, calculate
from src.services.reports import save_report
from src.utils.crypto import canonical

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def consume():
    with transaction() as cursor:
        job = one(cursor, "SELECT id,snapshot FROM runs WHERE status='queued' ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED")
        if not job:
            return
        try:
            snapshot = json.loads(job['snapshot'])
            result = calculate(snapshot)
        except LedgerMismatch as exc:
            cursor.execute("UPDATE runs SET status='failed', error=%s WHERE id=%s", (str(exc), job['id']))
        else:
            save_report(job['id'], snapshot, result)
            cursor.execute("UPDATE runs SET status='done', result=%s WHERE id=%s", (canonical(result), job['id']))
        logger.info('Processed run %s', job['id'])


if __name__ == '__main__':
    while True:
        try:
            CACHE.ping()
            consume()
            Path('/tmp/worker-heartbeat').touch()
        except Exception:
            logger.exception('Queue iteration will retry')
        time.sleep(1)
