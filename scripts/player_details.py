"""Verified, exact-item UT details, retained across daily EA ratings rebuilds."""
import json
from datetime import datetime, timezone
from pathlib import Path

COLS = ['eaId', 'baseId', 'ovr', 'pos', 'alt', 'club', 'league', 'nation',
        'gender', 'sm', 'wf', 'foot', 'height', 'age', 'stats', 'ps', 'pls', 'url']
# EA PlayStyle IDs from FUT.GG's FC 27 reference; they are not array indexes.
PS = {0:'Finesse Shot',1:'Chip Shot',2:'Power Shot',3:'Dead Ball',5:'Incisive Pass',
      6:'Pinged Pass',7:'Long Ball Pass',8:'Tiki Taka',9:'Whipped Pass',10:'Jockey',
      11:'Block',12:'Intercept',13:'Anticipate',14:'Slide Tackle',15:'Bruiser',
      16:'Technical',17:'Rapid',19:'First Touch',20:'Trickster',21:'Press Proven',
      22:'Quick Step',23:'Relentless',25:'Acrobatic',26:'Long Throw',28:'Far Throw',
      29:'Footwork',30:'Cross Claimer',31:'1v1 Close Down',32:'Far Reach',33:'Deflector',
      34:'Low Driven Shot',35:'Aerial Fortress',36:'Enforcer',37:'Gamechanger',
      38:'Inventive',39:'Precision Header'}

def styles(ids, plus=False):
    if not isinstance(ids, list) or any(i not in PS for i in ids):
        return None
    return ', '.join(PS[i] + ('+' if plus else '') for i in dict.fromkeys(ids))

def load(data):
    path = Path(data) / 'player-details.json'
    if not path.exists():
        return {}
    doc = json.loads(path.read_text(encoding='utf-8'))
    if doc.get('game') != 'FC 27' or doc.get('cols') != COLS:
        raise ValueError('Unknown exact player details format')
    return {str(r[0]): dict(zip(COLS, r), checkedAt=doc['updatedAt'], psAt=doc['updatedAt'])
            for r in doc['rows']}

def save(data, items):
    rows = [[p.get(c) for c in COLS] for _, p in sorted(items.items(), key=lambda kv:int(kv[0]))]
    path = Path(data) / 'player-details.json'
    old = json.loads(path.read_text()) if path.exists() else {}
    if old.get('rows') == rows:
        return
    doc = {'game':'FC 27', 'source':'FUT.GG exact FC 27 item metadata',
           'updatedAt':datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z'),
           'cols':COLS, 'rows':rows}
    path.write_text(json.dumps(doc, ensure_ascii=False, separators=(',',':'))+'\n', encoding='utf-8')

def merge(data, metadata):
    items = load(data)
    for key, record in metadata.items():
        # Older caches lack explicit checked-empty PlayStyle fields. They cannot erase verified data.
        if record.get('excluded') or not record.get('psAt') or 'pls' not in record or 'ps' not in record:
            continue
        if len(record.get('stats') or []) != 6 or not all(type(v) is int and 1 <= v <= 99 for v in record['stats']):
            continue
        previous = items.get(str(key), {})
        items[str(key)] = {**previous, **{k:v for k,v in record.items() if v is not None}}
    save(data, items)
    return items

def apply_base(roster, items):
    """Keep public names/URLs stable; replace card facts only for a matching base identity and rating."""
    ci = {c:i for i,c in enumerate(roster['cols'])}
    by_base = {}
    for p in items.values():
        by_base.setdefault(p.get('baseId'), []).append(p)
    changed = 0
    for row in roster['rows']:
        pid, rating = row[ci['id']], row[ci['ovr']]
        candidates = [p for p in by_base.get(pid, []) if p.get('ovr') == rating
                      and p.get('pos') == row[ci['pos']]
                      and (p['eaId'] == pid or p['eaId'] - pid in (50331648,67108864))]
        p = next((p for p in candidates if p['eaId'] == pid), candidates[0] if candidates else None)
        if not p:
            continue
        values = {k:p.get(k) for k in ('alt','club','league','nation','gender','sm','wf','height','age')}
        values['foot'] = {'Left':'L','Right':'R','L':'L','R':'R'}.get(p.get('foot'))
        values['psp'] = p.get('ps')
        values.update({'s'+str(i+1):v for i,v in enumerate(p['stats'])})
        for k,v in values.items():
            if k in ci and v is not None and row[ci[k]] != v:
                row[ci[k]] = v
                changed += 1
    return changed
