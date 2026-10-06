import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from futbin_prices import coins, parse_page, catalog, refresh, stamp


class FutbinTests(unittest.TestCase):
    def test_coin_formats(self):
        self.assertEqual(coins('1,295,000'), 1295000)
        self.assertEqual(coins('1.27M'), 1270000)
        self.assertEqual(coins('45.3K'), 45300)
        for value in ('0', 'Extinct', 'SBC cost', '-100', '20M'):
            self.assertIsNone(coins(value))

    def test_exact_card_and_market_price_only(self):
        page = '<div class="price-box platform-ps-only price-box-original-player" data-id="12"><div data-price-box-types="MARKET"></div><div class="lowest-price-1">1,500<img></div></div><div class="price-box platform-pc-only price-box-original-player" data-id="12"><div data-price-box-types="MARKET"></div><div class="lowest-price-1">2,500</div></div>'
        self.assertEqual(parse_page(page, 12), {'console': 1500, 'pc': 2500})
        self.assertEqual(parse_page(page, 13), {})
        self.assertEqual(parse_page(page.replace('MARKET', 'SBC'), 12), {})

    def test_catalog_must_match_an_exact_card(self):
        row = '<tr class="player-row"><a href="/27/player/12/player">Player</a><td class="table-price platform-ps-only"><div class="price bold">1.2K<img></div></td></tr>'
        quotes, _ = catalog(row, {}, {})
        self.assertEqual(quotes, {})
        quotes, _ = catalog(row, {'12': 50500123}, {})
        self.assertEqual(quotes['50500123']['prices']['console'], 1200)

    def test_primary_and_platform_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            (data / 'players.json').write_text(json.dumps({'cols': ['id', 'ovr'], 'rows': [[123, 80]]}))
            (data / 'card-ids.json').write_text(json.dumps({'12': 123}))
            row = '<tr class="player-row"><a href="/27/player/12/player">Player</a><td class="table-price platform-ps-only"><div class="price bold">1.2K<img></div></td></tr>'
            rows = [[123, 900, 1000, 0, 0], [456, 200, 300, 0, 0]]
            with patch('futbin_prices.fetch', return_value=row):
                metadata, _ = refresh(data, rows, [], pages=1)
            self.assertEqual(rows, [[123, 1200, 1000, 0, 0], [456, 200, 300, 0, 0]])
            self.assertEqual(metadata['123']['console']['src'], 'FUTBIN')
            self.assertNotIn('pc', metadata['123'])
            (data / 'futbin-prices.json').unlink()
            rows = [[123, 900, 1000, 0, 0]]
            with patch('futbin_prices.fetch', side_effect=PermissionError('denied')) as request:
                metadata, coverage = refresh(data, rows, [], pages=12)
            self.assertEqual(rows, [[123, 900, 1000, 0, 0]])
            self.assertEqual(metadata, {})
            self.assertEqual(request.call_count, 1)
            self.assertTrue(coverage['errors'])

    def test_rewards_and_expired_quotes_are_not_used(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            (data / 'players.json').write_text(json.dumps({'cols': ['id', 'ovr'], 'rows': []}))
            (data / 'card-ids.json').write_text('{}')
            (data / 'futbin-prices.json').write_text(json.dumps({'quotes': {'123': {'prices': {'console': 1200}, 'at': stamp()}, '456': {'prices': {'console': 1500}, 'at': '2020-01-01T00:00:00Z'}}}))
            rows = [[123, None, None, 3, 3], [456, 900, 1000, 0, 0]]
            with patch('futbin_prices.fetch', side_effect=RuntimeError('unavailable')):
                metadata, _ = refresh(data, rows, [], pages=1)
            self.assertEqual(metadata, {})
            self.assertEqual(rows, [[123, None, None, 3, 3], [456, 900, 1000, 0, 0]])


if __name__ == '__main__':
    unittest.main()
