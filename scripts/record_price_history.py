#!/usr/bin/env python3
"""Retain real source publications: hourly for seven days, daily for thirty. Also writes data/day-ago.json."""
import json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data'
def record(data,folder,tracked,now=None):
 now=now or datetime.now(timezone.utc).timestamp();folder.mkdir(parents=True,exist_ok=True)
 shards={}
 for row in data['rows']:
  if row[0] not in tracked:continue
  bucket=str(row[0]%64).zfill(2)
  if bucket not in shards:
   p=folder/(bucket+'.json');shards[bucket]=json.loads(p.read_text()) if p.exists() else {'game':'FC 27','items':{}}
  item=shards[bucket]['items'].setdefault(str(row[0]),{})
  for platform,col in [('console',1),('pc',2)]:
   if row[col+2]!=0 or not row[col]:continue
   at=data.get('quoteMetadata',{}).get(str(row[0]),{}).get(platform,{}).get('at') or data['publishedAt'][platform]
   t=datetime.fromisoformat(at.replace('Z','+00:00')).timestamp()
   if t>now+300 or t<now-30*86400:continue
   points=item.setdefault(platform,[])
   if not points or t>points[-1][0]+3500:points.append([int(t),row[col]])
   hourly={};daily={}
   for ts,price in points:
    if ts>=now-7*86400:hourly[ts//3600]=[ts,price]
    elif ts>=now-30*86400:daily[ts//86400]=[ts,price]
   item[platform]=sorted([*daily.values(),*hourly.values()])
 for bucket,shard in shards.items():
  shard['updatedAt']=data['retrievedAt'];(folder/(bucket+'.json')).write_text(json.dumps(shard,separators=(',',':'))+'\n')
 return len(shards)
def iso(ts):
 return datetime.fromtimestamp(ts,timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
def day_ago(folder,snaps_path,out_path,now=None):
 """Prices from about 24 hours ago, for the 24h change on the prices page (data/day-ago.json).
 Per card and platform: the recorded point closest to 24 h ago, if one is 20 to 28 h old. Console gaps are
 filled from the hourly market snapshots (every card worth 1,000+ coins, console only)."""
 now=now or datetime.now(timezone.utc).timestamp();aim,lo,hi=now-86400,now-28*3600,now-20*3600
 near=lambda pts:min(pts,key=lambda pt:abs(pt[0]-aim))
 out={}
 for p in sorted(folder.glob('[0-9][0-9].json')):
  for k,v in json.loads(p.read_text()).get('items',{}).items():
   for i,platform in enumerate(('console','pc')):
    pts=[pt for pt in v.get(platform,[]) if lo<=pt[0]<=hi]
    if pts:out.setdefault(int(k),[None,None])[i]=near(pts)[1]
 try:snaps=json.loads(Path(snaps_path).read_text())
 except (OSError,ValueError):snaps=[]
 timed=[(datetime.fromisoformat(s['t'].replace('Z','+00:00')).timestamp(),s) for s in snaps if s.get('t')]
 timed=[x for x in timed if lo<=x[0]<=hi]
 if timed:
  for k,price in near(timed)[1].get('p',{}).items():
   row=out.setdefault(int(k),[None,None])
   if row[0] is None and price:row[0]=int(price)
 rows=[[k,c,p] for k,(c,p) in sorted(out.items()) if c or p]
 data={'game':'FC 27','updatedAt':iso(now),'target':iso(aim),'cols':['id','console','pc'],'rows':rows}
 Path(out_path).write_text(json.dumps(data,separators=(',',':'))+'\n')
 return len(rows)
def main():
 roster=json.loads((DATA/'players.json').read_text());cols={k:i for i,k in enumerate(roster['cols'])}
 ids={r[cols['id']] for r in roster['rows'] if r[cols['ovr']]>=75}
 for name in ['newcards','legends']:
  ids.update(c.get('eaId') or c.get('gid') for c in json.loads((DATA/(name+'.json')).read_text()).get('cards',[]))
 feed=json.loads((DATA/'live-prices.json').read_text());print('Price history:',record(feed,DATA/'price-history',ids),'shards')
 print('Prices from a day ago:',day_ago(DATA/'price-history',DATA/'.cache'/'price-snaps.json',DATA/'day-ago.json'),'cards')
if __name__=='__main__':main()
