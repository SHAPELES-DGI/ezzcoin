import json
import tempfile
import unittest
from pathlib import Path
from card_catalog import extract, publish


class CatalogTests(unittest.TestCase):
    def test_exact_identity_prices_and_discovery(self):
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)
            (data / 'newcards.json').write_text(json.dumps({'cards': [{'fid': 12, 'name': 'Player', 'price': 999}]}))
            (data / 'card-ids.json').write_text(json.dumps({'12': 50500123}))
            def record(item, name):
                return {'eaId': item, 'baseId': 123, 'name': name, 'ovr': 87, 'pos': 'ST',
                        'version': 'Special', 'isSpecial': True, 'stats': [80] * 6,
                        'added': '2026-10-06', 'cardImageUrl': f'https://game-assets.fut.gg/2027/futgg-player-item-card/27-{item}.abc.webp'}
            metadata = {'50500123': record(50500123, 'Existing'), '50500124': record(50500124, 'New')}
            count = publish(data, metadata, {50500123: [50500123, None, None, 3, 3], 50500124: [50500124, 1500, 1600, 0, 0]}, '2026-10-06T12:00:00Z')
            self.assertEqual(count, 1)
            cards = json.loads((data / 'newcards.json').read_text())['cards']
            existing = next(c for c in cards if c.get('fid') == 12)
            self.assertNotIn('gid', existing)  # Existing URLs and watchlist keys survive.
            self.assertIsNone(existing['price'])  # Never retain old coins on an untradeable card.
            new = next(c for c in cards if c.get('gid') == 50500124)
            self.assertEqual(new['price'], 1500)
            before = (data / 'newcards.json').read_text()
            self.assertEqual(publish(data, metadata, {50500123: [50500123, None, None, 3, 3], 50500124: [50500124, 1500, 1600, 0, 0]}, '2026-10-06T12:00:00Z'), 0)
            self.assertEqual((data / 'newcards.json').read_text(), before)

    def test_wrong_edition_artwork_cannot_publish_a_new_card(self):
        player = {'eaId': 50500123, 'game': '27', 'commonName': 'Player', 'overall': 87,
                  'isSpecial': True, 'createdAt': '2026-10-06T12:00:00Z',
                  'faceStats': [{'rating': 80}] * 6,
                  'cardImageUrl': 'https://game-assets.fut.gg/2026/futgg-player-item-card/26-50500123.abc.webp'}
        record = extract(player)
        self.assertIsNone(record['cardImageUrl'])
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)
            self.assertEqual(publish(data, {'50500123': record}, {}, ''), 0)
            self.assertEqual(json.loads((data / 'newcards.json').read_text())['cards'], [])


if __name__ == '__main__':
    unittest.main()
