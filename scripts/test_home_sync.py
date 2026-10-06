import json
from pathlib import Path
import tempfile
import unittest
from datetime import datetime, timezone
from update_sbcs import parse
from sync_home_prices import synchronize


class HomeSyncTests(unittest.TestCase):
    def test_sbc_cost_is_not_score_and_expired_sets_are_removed(self):
        source = '$_TSR.router='
        for i in range(1, 5):
            end = '2020-01-01T00:00:00Z' if i == 4 else '2030-01-01T00:00:00Z'
            source += f'$R[{i}]={{id:{i},game:"27",eaId:{i},slug:"27-{i}-sbc",categoryEaId:1,name:"SBC {i}",endTime:"{end}",createdAt:"2026-10-06",url:"/sbc/players/27-{i}-sbc/",scoreRequirement:18750,cost:19780,costPc:22310,awards:$R[20]=[]}}'
        data = parse(source, datetime(2026, 10, 6, tzinfo=timezone.utc))
        self.assertEqual(len(data['sbcs']), 3)
        self.assertEqual(data['sbcs']['SBC 1']['cost'], 19780)
        self.assertEqual(data['sbcs']['SBC 1']['score'], 18750)
        self.assertEqual(data['sbcs']['SBC 1']['costPc'], 22310)
        with self.assertRaises(ValueError):
            parse('<html>Access denied</html>')

    def test_all_snapshots_use_exact_card_quote_without_faking_analysis_time(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = {
                'live-prices.json': {'rows': [[123, 1500, 1700, 0, 0], [456, None, None, 1, 1]], 'retrievedAt': '2026-10-06T19:00:00Z', 'publishedAt': {'console': '2026-10-06T18:59:00Z'}, 'source': 'FUT.GG'},
                'card-ids.json': {'12': 456},
                'players.json': {'cols': ['id', 'name', 'ovr', 'pos'], 'rows': [[123, 'Temwa Chawinga', 89, 'LM']]},
                'prices.json': {'players': {'123': {'price': 9999}, '1000000012': {'price': 12345}}},
                'topprices.json': {'players': {}}, 'trending.json': {'cards': [{'fid': 12, 'price': 12345}]},
                'snapshot.json': {'updatedAt': '2026-10-03', 'meta': [{'name': 'Chawinga', 'ovr': 89, 'pos': 'LM', 'price': 9999}, {'name': 'Unknown', 'ovr': 89, 'pos': 'LM', 'price': 9999}]}}
            for name, value in files.items():
                (root / name).write_text(json.dumps(value))
            synchronize(root)
            snapshot = json.loads((root / 'snapshot.json').read_text())
            self.assertEqual(snapshot['updatedAt'], '2026-10-03')
            self.assertEqual(snapshot['meta'][0]['price'], 1500)
            self.assertEqual(snapshot['meta'][0]['eaId'], 123)
            self.assertIsNone(snapshot['meta'][1]['price'])
            self.assertIsNone(json.loads((root / 'prices.json').read_text())['players']['1000000012']['price'])


if __name__ == '__main__':
    unittest.main()
