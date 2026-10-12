#!/usr/bin/env python3
"""Retain real source publications: hourly for seven days, daily for thirty."""
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
def main():
 roster=json.loads((DATA/'players.json').read_text());cols={k:i for i,k in enumerate(roster['cols'])}
 ids={r[cols['id']] for r in roster['rows'] if r[cols['ovr']]>=75}
 for name in ['newcards','legends']:
  ids.update(c.get('eaId') or c.get('gid') for c in json.loads((DATA/(name+'.json')).read_text()).get('cards',[]))
 feed=json.loads((DATA/'live-prices.json').read_text());print('Price history:',record(feed,DATA/'price-history',ids),'shards')
if __name__=='__main__':main()
