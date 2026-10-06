#!/usr/bin/env python3
"""Synchronize legacy Home/trading snapshots to the shared exact-item quotes."""
import json
from pathlib import Path
import re
import unicodedata

DATA = Path(__file__).resolve().parents[1] / 'data'


def read(name):
    return json.loads((DATA / name).read_text())


def write(name, value):
    path = DATA / name
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n')
    temporary.replace(path)


def normalized(name):
    return re.sub(r'[^a-z0-9]+', ' ', unicodedata.normalize('NFKD', name or '').encode('ascii', 'ignore').decode().lower()).strip()


def synchronize(data=DATA):
    global DATA
    DATA = data
    live = read('live-prices.json')
    rows = {r[0]: r for r in live['rows']}
    ids = read('card-ids.json')
    def quote(item):
        row = rows.get(int(item)) if item else None
        if row is None:
            return None
        meta = live.get('quoteMetadata', {}).get(str(item), {}).get('console', {})
        return {'eaId': int(item), 'price': row[1] if row[3] == 0 else None, 'priceState': row[3],
                'at': meta.get('at', live['publishedAt']['console']), 'src': meta.get('src', live['source'])}
    for name in ('prices.json', 'topprices.json'):
        payload = read(name)
        for key, player in payload.get('players', {}).items():
            item = ids.get(str(int(key) - 1000000000)) if int(key) >= 1000000000 else int(key)
            current = quote(item)
            if current:
                player.update(current)
        payload['updatedAt'] = live['retrievedAt']
        write(name, payload)
    trending = read('trending.json')
    for card in trending.get('cards', []):
        item = ids.get(str(card.get('fid'))) or card.get('eaId')
        current = quote(item)
        if current:
            card.update(current)
            card['priceAt'] = current['at']
    write('trending.json', trending)
    roster = read('players.json')
    cols = {col: n for n, col in enumerate(roster['cols'])}
    players = [{'id': r[cols['id']], 'name': r[cols['name']], 'ovr': r[cols['ovr']], 'pos': r[cols['pos']]} for r in roster['rows']]
    snapshot = read('snapshot.json')
    for card in snapshot.get('meta', []):
        name = normalized(card['name'])
        candidates = [p for p in players if int(p['ovr']) == int(card['ovr']) and p['pos'] == card['pos'] and
                      (normalized(p['name']) == name or normalized(p['name']).endswith(' ' + name))]
        current = quote(card.get('eaId') or (candidates[0]['id'] if len(candidates) == 1 else None))
        # Do not keep an old snapshot price when the exact card cannot be resolved.
        card['price'] = None
        if current:
            card.update(current)
            card['priceAt'] = current['at']
        card['note'] = 'Console · ' + current['src'] if current else 'Exact card price unavailable'
    # The editorial market read keeps its original timestamp.
    snapshot['pricesUpdatedAt'] = live['retrievedAt']
    write('snapshot.json', snapshot)
    print('Home, watchlist, trending and trading quotes synchronized:', live['retrievedAt'])


if __name__ == '__main__':
    synchronize()
