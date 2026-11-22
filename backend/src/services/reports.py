import csv
import io
from pathlib import Path

REPORTS = Path('/reports')


def csv_payload(snapshot, result):
    out = io.StringIO(newline='')
    writer = csv.writer(out)
    writer.writerow(['器材族', '单位', '出借馆', '入借馆', '签领', '冲销', '有效调借', '反向有效调借', '双向相抵', '本方向差额'])
    halls = {item['code']: item['name'] for item in snapshot['halls']}
    for item in snapshot['instruments']:
        family = result['family'][item['code']]
        for row in family['directions']:
            source, destination = row['source'], row['destination']
            opposite = family['matrix'][destination][source]
            writer.writerow([item['name'], item['unit'], halls[source], halls[destination], row['loan'], row['reversal'],
                             row['effective'], opposite, max(0, min(row['effective'], opposite)), row['effective'] - opposite])
    return out.getvalue().encode('utf-8-sig')


def report_path(run_id):
    return REPORTS / f'flow-{run_id}.csv'


def save_report(run_id, snapshot, result):
    path = report_path(run_id)
    temp = path.with_suffix('.tmp')
    temp.write_bytes(csv_payload(snapshot, result))
    temp.replace(path)
