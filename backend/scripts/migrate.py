from pathlib import Path

from src.models.db import transaction

with transaction() as cursor:
    for path in sorted(Path('/app/migrations').glob('*.sql')):
        for sql in path.read_text().split(';'):
            if sql.strip():
                cursor.execute(sql)
