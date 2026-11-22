from collections import defaultdict
from itertools import combinations, permutations

from src.constants.domain import ReceiptKind
from src.utils.crypto import signed


class LedgerMismatch(ValueError):
    pass


def calculate(snapshot):
    halls = [item['code'] for item in snapshot['halls']]
    originals = {row['id']: row for row in snapshot['originals']}
    signed_events = defaultdict(lambda: [0, 0])
    reversals = set()
    for row in snapshot['receipts']:
        if not signed(row):
            raise LedgerMismatch(f'{row["reference"]} 的签名校验失败')
        is_reversal = row['kind'] == ReceiptKind.REVERSAL
        if is_reversal:
            original = originals.get(row['original_id'])
            route_fields = ('source', 'destination', 'instrument', 'quantity')
            if (not original or original['kind'] != ReceiptKind.LOAN or not signed(original)
                    or original['effective_on'] > row['effective_on'] or original['id'] in reversals
                    or any(original[field] != row[field] for field in route_fields)):
                raise LedgerMismatch(f'{row["reference"]} 与原签领无法配对')
            reversals.add(original['id'])
        direction = (row['instrument'], row['source'], row['destination'])
        signed_events[direction][int(is_reversal)] += row['quantity']

    families = {}
    aggregate = matrix(halls)
    for item in snapshot['instruments']:
        family = item['code']
        directional = matrix(halls)
        directions = []
        for source, destination in permutations(halls, 2):
            loan, reversal = signed_events[family, source, destination]
            effective = loan - reversal
            directional[source][destination] = effective
            aggregate[source][destination] += effective
            directions.append({'source': source, 'destination': destination, 'loan': loan,
                               'reversal': reversal, 'effective': effective})
        pairs = []
        for left, right in combinations(halls, 2):
            forward, backward = directional[left][right], directional[right][left]
            if forward or backward:
                pairs.append({'left': left, 'right': right, 'forward': forward, 'backward': backward,
                              'matched': max(0, min(forward, backward)), 'balance': forward - backward})
        families[family] = {**margins(halls, directional), 'pairs': pairs, 'directions': directions}

    result = margins(halls, aggregate)
    result['family'] = families
    result['matched'] = sum(pair['matched'] for family in families.values() for pair in family['pairs'])
    result['loan'] = sum(counts[0] for counts in signed_events.values())
    result['reversal'] = sum(counts[1] for counts in signed_events.values())
    result['receipt_count'] = len(snapshot['receipts'])
    result['verified'] = (result['net_total'] == 0 and result['total_in'] == result['total_out']
                          == result['loan'] - result['reversal'])
    if not result['verified']:
        raise LedgerMismatch('签名净额与矩阵边际不守恒')
    return result


def matrix(halls):
    return {source: dict.fromkeys(halls, 0) for source in halls}


def margins(halls, directional):
    outgoing = {source: sum(directional[source].values()) for source in halls}
    incoming = {destination: sum(directional[source][destination] for source in halls) for destination in halls}
    hall_totals = {hall: {'in': incoming[hall], 'out': outgoing[hall], 'net': incoming[hall] - outgoing[hall]}
                   for hall in halls}
    return {'matrix': directional, 'halls': hall_totals, 'total_in': sum(incoming.values()),
            'total_out': sum(outgoing.values()), 'net_total': sum(row['net'] for row in hall_totals.values())}
