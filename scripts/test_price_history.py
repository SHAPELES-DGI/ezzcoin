import json,tempfile,unittest
from pathlib import Path
from record_price_history import record,day_ago
class HistoryTests(unittest.TestCase):
 def test_source_time_no_duplicates_missing_and_platforms(self):
  now=1791828000
  feed={'retrievedAt':'2026-10-12T18:00:00Z','publishedAt':{'console':'2026-10-12T17:00:00Z','pc':'2026-10-12T17:10:00Z'},'rows':[[123,1000,1200,0,0],[124,None,1000,1,0]]}
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);record(feed,root,{123,124},now=now);record(feed,root,{123,124},now=now)
   item=json.loads((root/'59.json').read_text())['items']['123'];self.assertEqual(len(item['console']),1);self.assertNotEqual(item['console'][0][0],item['pc'][0][0])
   self.assertEqual(item['console'][0][1],1000);missing=json.loads((root/'60.json').read_text())['items']['124'];self.assertNotIn('console',missing)
 def test_retention_and_future(self):
  now=1791828000
  feed={'retrievedAt':'2026-10-12T18:00:00Z','publishedAt':{'console':'2026-10-12T17:00:00Z','pc':'2026-10-12T17:10:00Z'},'rows':[[123,1000,None,0,0]]}
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);old={'items':{'123':{'console':[[now-40*86400,500],[now-10*86400,600],[now-10*86400+3600,650],[now-86400,700]]}}}
   (root/'59.json').write_text(json.dumps(old));record(feed,root,{123},now=now);p=json.loads((root/'59.json').read_text())['items']['123']['console'];self.assertFalse(any(t<now-30*86400 for t,v in p));self.assertEqual(len([t for t,v in p if t<now-7*86400]),1)
 def test_day_ago_reference(self):
  now=1791828000
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder)
   # Card 123: points 30 h, 23 h and 2 h old -> the 23 h one. Card 124: only 2 h old -> console from the snapshots.
   (root/'59.json').write_text(json.dumps({'items':{'123':{'console':[[now-30*3600,900],[now-23*3600,1000],[now-7200,1200]],'pc':[[now-25*3600,1500]]}}}))
   (root/'60.json').write_text(json.dumps({'items':{'124':{'console':[[now-7200,5000]]}}}))
   iso=lambda ts:__import__('datetime').datetime.fromtimestamp(ts,__import__('datetime').timezone.utc).isoformat().replace('+00:00','Z')
   snaps=root/'snaps.json';snaps.write_text(json.dumps([{'t':iso(now-24*3600-600),'p':{'124':4000,'123':777,'125':2000}},{'t':iso(now-3600),'p':{'124':5100}}]))
   out=root/'day-ago.json';n=day_ago(root,snaps,out,now=now);d=json.loads(out.read_text())
   rows={r[0]:r[1:] for r in d['rows']}
   self.assertEqual(rows[123],[1000,1500]);self.assertEqual(rows[124],[4000,None]);self.assertEqual(rows[125],[2000,None]);self.assertEqual(n,3)
   self.assertEqual(d['cols'],['id','console','pc'])
if __name__=='__main__':unittest.main()
