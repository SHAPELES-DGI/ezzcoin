"""Audit every generated player page against exact item facts and local destinations."""
import html
import json
import re
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.argv = [sys.argv[0], str(ROOT)]
import build_pages as build
from player_details import load, apply_base
from meta import meta

class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(); self.tags=[]; self.feed(text)
    def handle_starttag(self, tag, attrs):
        self.tags.append((tag,dict(attrs)))

class PlayerPages(unittest.TestCase):
    def test_complete_catalogue_and_destinations(self):
        pages=list((ROOT/'p').glob('*/index.html'))
        pages=[p for p in pages if p.parent.name!='credits']
        roster=json.loads((ROOT/'data/players.json').read_text())
        expected_base={str(r[roster['cols'].index('id')]) for r in roster['rows'] if r[roster['cols'].index('ovr')]>=75}
        actual_base=set()
        for path in pages:
            text=path.read_text(); parsed=Page(text)
            self.assertNotRegex(text, r'\b(?:NaN|undefined)\b', str(path))
            ids=[a['id'] for _,a in parsed.tags if a.get('id')]
            self.assertEqual(len(ids),len(set(ids)),str(path))
            self.assertEqual(ids.count('px'),1,str(path))
            page_id=int(path.parent.name.rsplit('-',1)[1])
            if page_id<1000000000: actual_base.add(str(page_id))
            px=next(a for _,a in parsed.tags if a.get('id')=='px')
            self.assertIn('data-item',px,str(path))
            srcs=[a['src'].split('?')[0] for t,a in parsed.tags if t=='script' and 'src' in a]
            for name in ['market-data.js','player-tools.js','price-history.js','p/chem.js']:
                self.assertEqual(sum(s.endswith(name) for s in srcs),1,(str(path),name))
            for tag,attrs in parsed.tags:
                for key in ('href','src'):
                    value=attrs.get(key,''); url=urlsplit(value)
                    if not value or url.scheme or url.netloc or value.startswith('#'): continue
                    target=(path.parent/unquote(url.path)).resolve()
                    if value.split('?')[0].endswith('/') or target.is_dir(): target=target/'index.html'
                    self.assertTrue(target.exists(),(str(path),value))
        self.assertEqual(actual_base,expected_base)
        print(f'Checked {len(pages)} player pages: unique IDs, scripts, catalogue coverage and every local link/asset.')

    def test_exact_stats_styles_and_meta(self):
        details=load(ROOT/'data'); by_base={}
        for p in details.values(): by_base.setdefault(p['baseId'],[]).append(p)
        checked=0
        for path in (ROOT/'p').glob('*/index.html'):
            if path.parent.name=='credits': continue
            text=path.read_text(); attrs=next(a for _,a in Page(text).tags if a.get('id')=='chem') if 'id="chem"' in text else None
            if not attrs: continue
            px=next(a for _,a in Page(text).tags if a.get('id')=='px')
            item=px['data-item']; p=details.get(item)
            if not p or p.get('ovr') != int(attrs['data-ovr']): continue
            self.assertEqual(json.loads(attrs['data-s']),p['stats'],str(path))
            self.assertEqual(attrs['data-ps'],p['ps'],str(path))
            self.assertEqual(set(attrs['data-alt'].split(',')),set(p['alt'].split(',')),str(path))
            expected=meta(attrs['data-pos'],attrs['data-alt'],p['stats'],p['sm'],p['wf'],p['ps'])
            for pos,score in expected.items():
                self.assertIn(f'<small>{pos}</small><strong>{score}</strong>',text,str(path))
            regular=text.split('aria-label="Regular PlayStyles"',1)[-1].split('</div></div>',1)[0] if 'aria-label="Regular PlayStyles"' in text else ''
            for plus in p['ps'].split(', '):
                if plus: self.assertNotIn('>'+html.escape(plus.rstrip('+'))+'</span>',regular,str(path))
            checked+=1
        print(f'Checked exact stats, own PlayStyles+ and every position meta on {checked} matched pages.')

    def test_goalkeeper_import_never_uses_outfield_pace(self):
        from build_players import row
        p={'id':1,'firstName':'Keeper','position':{'shortLabel':'GK'},'stats':{'pac':90,'gkDiving':87,'gkHandling':85,'gkKicking':70,'gkReflexes':88,'gkPositioning':85,'acceleration':40,'sprintSpeed':50}}
        self.assertEqual(row(p,0)[20],44)
        p['stats'].pop('acceleration');p['stats'].pop('sprintSpeed')
        self.assertIsNone(row(p,0)[20])

if __name__=='__main__': unittest.main(argv=[sys.argv[0]])
