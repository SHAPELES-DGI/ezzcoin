#!/usr/bin/env python3
"""Read FC 27 SBC sets and actual solution costs from public FUT.GG page data.

Parse data fields only; never execute the page's JavaScript. Item Score is kept
separate from coin cost. Failed/empty responses leave the last good file intact.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess

DATA = Path(__file__).resolve().parents[1] / 'data'
STRING = r'"(?:\\.|[^"\\])*"'
SCALAR = re.compile(r'\b([A-Za-z][A-Za-z0-9]*):(' + STRING + r'|-?\d+(?:\.\d+)?|null|!0|!1)(?=[,}]|$)')


def fields(prefix):
    result = {}
    for key, value in SCALAR.findall(prefix):
        result[key] = True if value == '!0' else False if value == '!1' else json.loads(value)
    return result


def parse(source, now=None):
    now = now or datetime.now(timezone.utc)
    if '$_TSR.router=' not in source:
        raise ValueError('SBC page data missing; retaining previous SBCs')
    source = source[source.index('$_TSR.router='):]
    segments = {}
    # All required challenge scalar fields occur before its nested awards data.
    pattern = r'\$R\[\d+\]=\{id:\d+,eaId:\d+,game:"27",challengeType:'
    for match in re.finditer(pattern, source):
        chunk = source[match.start():]
        end = chunk.find(',awards:$R')
        if end < 0:
            continue
        chunk = chunk[:end]
        values = fields(chunk)
        requirement = re.search(r'requirementsText:\$R\[\d+\]=(\[(?:' + STRING + r'(?:,|(?=\])))*\])', chunk)
        req = json.loads(requirement[1]) if requirement else []
        segment = {'id': values['eaId'], 'name': values.get('name', 'Squad'),
                   'req': '; '.join(req), 'score': values.get('scoreRequirement'),
                   'cost': values.get('cheapestSolutionPrice'), 'costPc': values.get('cheapestSolutionPricePc'),
                   'squadUrl': 'https://www.fut.gg' + values['cheapestSolutionUrl'] if values.get('cheapestSolutionUrl') else None,
                   'players': []}
        segments.setdefault(values['setEaId'], {})[segment['id']] = segment
    sets = {}
    pattern = r'\$R\[\d+\]=\{id:\d+,game:"27",eaId:\d+,slug:"27-\d+-[^"\n]+",categoryEaId:'
    for match in re.finditer(pattern, source):
        chunk = source[match.start():]
        end = chunk.find(',awards:$R')
        if end < 0:
            continue
        values = fields(chunk[:end])
        expiry = values.get('endTime')
        if expiry and datetime.fromisoformat(expiry.replace('Z', '+00:00')) <= now:
            continue
        if not values.get('url', '').startswith('/sbc/'):
            continue
        at = now.isoformat(timespec='seconds').replace('+00:00', 'Z')
        sets[values['eaId']] = {'id': values['eaId'], 'name': values['name'], 'category': values['categoryEaId'],
             'url': 'https://www.fut.gg' + values['url'], 'src': 'FUT.GG', 'at': at,
             'cost': values.get('cost'), 'costPc': values.get('costPc'), 'score': values.get('scoreRequirement'),
             'endTime': expiry, 'added': values.get('createdAt'), 'repeatable': values.get('isRepeatable', False),
             'segments': list(segments.get(values['eaId'], {}).values()),
             'note': values.get('description', '')}
    if len(sets) < 3:
        raise ValueError('Incomplete SBC catalog; retaining previous SBCs')
    cards = sorted(sets.values(), key=lambda item: item.get('added') or '', reverse=True)
    return {'game': 'FC 27', 'updatedAt': now.isoformat(timespec='seconds').replace('+00:00', 'Z'),
            'source': 'FUT.GG', 'sourceUrl': 'https://www.fut.gg/sbc/', 'automatic': True,
            'sbcs': {item['name']: item for item in cards}}


def main():
    response = subprocess.run(['curl', '-sSL', '--max-time', '30', '-w', '\n%{http_code}', 'https://www.fut.gg/sbc/'], capture_output=True, text=True)
    if response.returncode:
        raise RuntimeError('SBC source unavailable; retaining previous SBCs')
    body, code = response.stdout.rsplit('\n', 1)
    if code != '200':
        raise RuntimeError('SBC source HTTP ' + code + '; retaining previous SBCs')
    output = parse(body)
    path = DATA / 'sbcsolutions.json'
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(output, ensure_ascii=False, separators=(',', ':')) + '\n')
    temporary.replace(path)
    print('SBCs refreshed:', len(output['sbcs']), 'active sets; console and PC solution costs')


if __name__ == '__main__':
    main()
