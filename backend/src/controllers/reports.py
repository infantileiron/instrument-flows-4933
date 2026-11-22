from fastapi import HTTPException, Response

from src.constants.domain import RunStatus
from src.models.db import transaction
from src.services.plans import get_run
from src.services.reports import csv_payload, report_path


def download(run_id, user):
    with transaction() as cursor:
        run, snapshot = get_run(cursor, run_id, user)
    if run['status'] != RunStatus.DONE:
        raise HTTPException(409, '透视尚未完成')
    path = report_path(run_id)
    try:
        content = path.read_bytes()
    except FileNotFoundError:
        content = csv_payload(snapshot, run['result'])
    return Response(content, media_type='text/csv',
                    headers={'Content-Disposition': f'attachment; filename="flow-{run_id}.csv"'})
