"""Read public FC 27 listings; retain FUT.GG quotes for gaps and failures.

FUTBIN has paginated HTML, not FUT.GG's bulk feed. Bound each run, rotate through
the catalog and prioritize displayed cards. Never retry security/rate denials.
"""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from html import unescape
from html.parser import HTMLParser
import json
import re
import subprocess
import time
import unicodedata


def stamp():
    return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def coins(text):
    value = re.sub(r'\s+', '', unescape(text)).replace(',', '').upper()
    if not re.fullmatch(r'\d+(?:\.\d+)?[KM]?', value):
        return None
    try:
        multiplier = 1000 if value.endswith('K') else 1000000 if value.endswith('M') else 1
        amount = Decimal(value.rstrip('KM')) * multiplier
        return int(amount) if amount == int(amount) and 0 < amount <= 15000000 else None
    except InvalidOperation:
        return None


def fetch(url):
    result = subprocess.run(['curl', '-sSL', '--max-time', '25', '-w', '\n%{http_code}', url], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError('FUTBIN request unavailable')
    body, status = result.stdout.rsplit('\n', 1)
    if status in ('401', '403', '429') or re.search(r'<title>\s*(?:Just a moment|Access denied)', body, re.I):
        raise PermissionError('FUTBIN denied/rate-limited the request; using FUT.GG')
    if status != '200':
        raise RuntimeError('FUTBIN HTTP ' + status)
    return body


class PriceBoxes(HTMLParser):
    VOID = {'img', 'input', 'link', 'meta', 'br', 'hr', 'source', 'area', 'wbr', 'embed'}
    def __init__(self, fid):
        super().__init__()
        self.fid = str(fid)
        self.stack = []
        self.prices = {}
        self.box = None
        self.capture = None
        self.text = []
        self.market = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = set(attrs.get('class', '').split())
        depth = len(self.stack)
        if 'price-box-original-player' in classes and attrs.get('data-id') == self.fid:
            platform = 'console' if 'platform-ps-only' in classes else 'pc' if 'platform-pc-only' in classes else None
            self.box = (depth, platform)
            self.market = False
        if self.box:
            if attrs.get('data-price-box-types') == 'MARKET':
                self.market = True
            if 'lowest-price-1' in classes:
                self.capture, self.text = depth, []
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_data(self, data):
        if self.capture is not None:
            self.text.append(data)

    def handle_endtag(self, tag):
        if tag in self.VOID or tag not in self.stack:
            return
        while self.stack and self.stack[-1] != tag:
            self.stack.pop()
        self.stack.pop()
        depth = len(self.stack)
        if self.capture == depth:
            price = coins(''.join(self.text))
            if self.market and price and self.box[1]:
                self.prices[self.box[1]] = price
            self.capture = None
        if self.box and depth == self.box[0]:
            self.box = None


def parse_page(source, fid):
    parser = PriceBoxes(fid)
    parser.feed(source)
    return parser.prices


def text(element):
    return unescape(re.sub(r'<[^>]+>', '', element)).strip()


def catalog(source, ids, base_rows):
    matches = {}
    for row in re.findall(r'<tr class="player-row\b.*?</tr>', source, re.S):
        link = re.search(r'href="/27/player/(\d+)/', row)
        if not link:
            continue
        fid = link[1]
        item = ids.get(fid)
        if not item:
            # Only plain base-card frames can use the base portrait ID as item ID.
            face = re.search(r'/content/fifa27/img/players/(\d+)\.png', row)
            frame = re.search(r'/cards/tiny/(\d+)_([^.?]+)', row)
            rating = re.search(r'class="rating-square"[^>]*>(\d+)', row)
            if face and frame and rating and frame[1] in ('0', '1', '2', '3', '4', '5'):
                base = int(face[1])
                if base_rows.get(base) == int(rating[1]):
                    item = base
                    ids[fid] = base
        if not item:
            continue
        prices = {}
        for platform, css in [('console', 'ps'), ('pc', 'pc')]:
            cell = re.search(r'<td class="[^"]*table-price[^"]*platform-' + css + r'-only[^\"]*">(.*?)</td>', row, re.S)
            value = re.search(r'<div class="price\s[^\"]*">(.*?)<img', cell[1], re.S) if cell else None
            price = coins(text(value[1])) if value else None
            if price:
                prices[platform] = price
        if prices:
            path = re.search(r'href="(/27/player/[^\"]+)"', row)[1]
            matches[str(item)] = {'fid': int(fid), 'prices': prices, 'at': stamp(), 'url': 'https://www.futbin.com' + path}
    last = max([int(n) for n in re.findall(r'/27/players\?page=(\d+)', source)] or [1])
    return matches, last


def refresh(data, rows, home, pages=12, player_pages=20):
    cache_path = data / 'futbin-prices.json'
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {'quotes': {}, 'cursor': 2}
    ids = json.loads((data / 'card-ids.json').read_text())
    # Persist newly verified FUTBIN base-card IDs separately from site's key mapping.
    ids = {k: v for k, v in ids.items() if k.isdigit() and int(k) < 1000000} | cache.get('ids', {})
    roster = json.loads((data / 'players.json').read_text())
    cols = {name: i for i, name in enumerate(roster['cols'])}
    bases = {int(r[cols['id']]): int(r[cols['ovr']]) for r in roster['rows'] if r[cols['ovr']]}
    quotes = cache.get('quotes', {})
    errors = []
    checked = 0
    deadline = time.monotonic() + 240
    try:
        matches, last = catalog(fetch('https://www.futbin.com/27/players'), ids, bases)
        quotes.update(matches)
        checked += 1
        cursor = max(2, min(int(cache.get('cursor', 2)), last))
        for _ in range(max(0, pages - 1)):
            if time.monotonic() >= deadline:
                break
            time.sleep(0.3)
            found, _ = catalog(fetch(f'https://www.futbin.com/27/players?page={cursor}'), ids, bases)
            quotes.update(found)
            checked += 1
            cursor = 2 if cursor >= last else cursor + 1
        cache['cursor'] = cursor
        inverse = {}
        for fid, item in ids.items():
            inverse.setdefault(int(item), int(fid))
        # The newest visible cards take precedence over rotating catalog pages.
        done = set()
        market_ids = {r[0] for r in rows if r[3] == 0 or r[4] == 0}
        exact = json.loads((data / 'card-ids.json').read_text())
        for card in home:
            if time.monotonic() >= deadline:
                break
            key = str(card.get('gid') or card.get('fid'))
            item = exact.get(key) or card.get('eaId') or card.get('gid')
            fid = card.get('fid') or inverse.get(item)
            if not fid or not item or item not in market_ids or item in done or len(done) >= player_pages:
                continue
            done.add(item)
            time.sleep(0.3)
            try:
                slug = re.sub(r'[^a-z0-9]+', '-', unicodedata.normalize('NFKD', card['name']).encode('ascii', 'ignore').decode().lower()).strip('-') or 'player'
                url = f'https://www.futbin.com/27/player/{fid}/{slug}'
                prices = parse_page(fetch(url), fid)
                if prices:
                    quotes[str(item)] = {'fid': fid, 'prices': prices, 'at': stamp(), 'url': url}
                checked += 1
            except RuntimeError as error:
                errors.append(str(error))
    except (PermissionError, RuntimeError) as error:
        errors.append(str(error))
    cutoff = time.time() - 20 * 60
    fresh = {}
    for item, quote in quotes.items():
        try:
            if datetime.fromisoformat(quote['at'].replace('Z', '+00:00')).timestamp() >= cutoff:
                fresh[item] = quote
        except (KeyError, ValueError):
            pass
    cache.update({'quotes': fresh, 'ids': ids, 'checkedAt': stamp(), 'pagesChecked': checked, 'errors': errors})
    cache_path.write_text(json.dumps(cache, separators=(',', ':')) + '\n')
    metadata = {}
    count = {'console': 0, 'pc': 0}
    for row in rows:
        quote = fresh.get(str(row[0]))
        if not quote:
            continue
        for platform, price_col, state_col in [('console', 1, 3), ('pc', 2, 4)]:
            price = quote['prices'].get(platform)
            # Never price SBCs, objectives or rewards as transferable market cards.
            if price and row[state_col] == 0:
                row[price_col] = price
                metadata.setdefault(str(row[0]), {})[platform] = {'src': 'FUTBIN', 'at': quote['at'], 'url': quote.get('url', 'https://www.futbin.com/27/players')}
                count[platform] += 1
    return metadata, {**count, 'pagesChecked': checked, 'errors': errors, 'catalogCursor': cache.get('cursor')}
