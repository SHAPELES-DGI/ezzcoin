#!/usr/bin/env python3
"""Publish live Evolution rules and exact Item Scores from public catalogue data."""
import argparse,json,re,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
from public_page_data import object_after
ROOT=Path(__file__).resolve().parents[1]
def fetch(url):
 r=subprocess.run(['curl','-fsSL','--max-time','30',url],capture_output=True,text=True)
 if r.returncode:raise ValueError('Public catalogue unavailable')
 return r.stdout
def compact(p):
 return {**{k:p.get(k) for k in ['eaId','basePlayerEaId','overall','gradingScore','position','alternativePositions','positionId','alternativePositionIds','rarityEaId','birthDate','playStyleEaIds','playStylePlusEaIds','isIcon','isHero','extraLeagueChemistry','extraNationChemistry','extraClubChemistry','extraSquadLeagueChemistry','extraSquadNationChemistry','isFullChemistry','skillMoves','weakFoot']},
 'name':p.get('commonName') or p.get('cardName'),'stats':[x['rating'] for x in p.get('faceStats',[])],
 'url':p.get('url'),'image':p.get('cardImageUrl'),'club':(p.get('club') or {}).get('name'),'clubId':p.get('uniqueClubEaId'),
 'league':(p.get('league') or {}).get('name'),'nation':(p.get('nation') or {}).get('name'),
 'attributes':{k:v for k,v in p.items() if k.startswith('attribute') and isinstance(v,(int,float))}}
def parse(source):
 refs={};out=[]
 for m in re.finditer(r'\$R\[\d+\]=\{evolution:\$R\[\d+\]=',source):
  entry=object_after(source,m.start()+m[0].index('{'),refs);e=entry['evolution']
  if e.get('game')!='27' or e.get('isExpired') or e.get('hideFromListings'):continue
  out.append({**{k:e.get(k) for k in ['id','name','description','coinsCost','tokenCost','endTime','endSubmissionTime','requirements','requirementsText','levels','totalUpgrades','totalUpgradesText','hasUpgradeChoices','bestPathChoices','allowedPriorEvolutionIds','repeatabilityCount']},
   'url':'https://www.fut.gg'+e['url'],'example':{'before':compact(entry['basePlayer']),'after':compact(entry['upgradedPlayer'])},
   'suggestedIds':[int(x.split('_')[0]) for x in e.get('trendingPlayersIds',[])[:8]]})
 if len(out)<3:raise ValueError('Incomplete Evolution catalogue')
 return out
def playstyle_names(evolutions):
 names={}
 for e in evolutions:
  for level in e.get('levels',[]):
   for group in [level]+level.get('upgradeOptions',[]):
    upgrades=[u for u in group.get('upgrades',[]) if u['upgrade']=='play_style']
    labels=[u for u in group.get('totalUpgradesText',[]) if u['label']=='PlayStyle']
    if len(upgrades)==len(labels):
     for u,label in zip(upgrades,labels):names[str(u['value'])]=label['value']
 return names
def main():
 a=argparse.ArgumentParser();a.add_argument('--source');a.add_argument('--batches',type=int,default=6);a.add_argument('--details',type=int,default=12);a.add_argument('--min-age',type=int,default=0);args=a.parse_args()
 cache=ROOT/'data/evolutions.json'
 if args.min_age and cache.exists():
  try:
   age=datetime.now(timezone.utc).timestamp()-datetime.fromisoformat(json.loads(cache.read_text())['updatedAt'].replace('Z','+00:00')).timestamp()
   if 0<=age<args.min_age:
    print('Builder rules are current; skipping refresh');return
  except (ValueError,KeyError):pass
 es=parse(Path(args.source).read_text() if args.source else fetch('https://www.fut.gg/evolutions/'))
 (ROOT/'data/evolutions.json').write_text(json.dumps({'game':'FC 27','updatedAt':datetime.now(timezone.utc).isoformat(),'source':'FUT.GG','playstyleNames':playstyle_names(es),'evolutions':es},separators=(',',':'))+'\n')
 path=ROOT/'data/builder-items.json';items=json.loads(path.read_text()).get('items',{}) if path.exists() else {}
 for e in es:
  p=e['example']['before'];previous=items.get(str(p['eaId']),{});p['attributes']={**previous.get('attributes',{}),**p.get('attributes',{})};items[str(p['eaId'])]=p
 roster=json.loads((ROOT/'data/players.json').read_text());ci={k:i for i,k in enumerate(roster['cols'])}
 price=json.loads((ROOT/'data/live-prices.json').read_text());prices={r[0]:r[1] for r in price['rows'] if r[3]==0 and r[1]}
 wanted=[]
 # Exact Item Score and metadata for affordable solver candidates in every quality.
 for rating in range(45,96):
  wanted += [r[ci['id']] for r in sorted([r for r in roster['rows'] if r[ci['ovr']]==rating and r[ci['id']] in prices],key=lambda r:prices[r[ci['id']]])[:4]]
 for e in es:wanted+=e['suggestedIds']
 wanted=list(dict.fromkeys(wanted));cursor=int(json.loads(path.read_text()).get('cursor',0)) if path.exists() else 0
 selected=[i for i in wanted if str(i) not in items]+wanted[cursor:cursor+30]
 errors=[]
 for n in range(0,min(len(selected),max(0,args.batches)*30),30):
  ids=selected[n:n+30]
  try:
   data=json.loads(fetch('https://www.fut.gg/api/fut/players/v2/27/?ids='+','.join(map(str,ids))))['data']
   for p in data:
    if p.get('game')!='27' or p.get('eaId') not in ids:raise ValueError('Wrong item response')
    entry=compact(p);entry['attributes']={**items.get(str(p['eaId']),{}).get('attributes',{}),**entry['attributes']};items[str(p['eaId'])]=entry
  except (ValueError,KeyError) as e:errors.append(str(e))
  time.sleep(.3)
 # Rich item definitions provide attributes needed for exact Evolution calculations.
 for key,p in list(items.items()):
  if args.details<=0:break
  url=p.get('url')
  if len(p.get('attributes',{}))>=30 or not url or not url.startswith('/players/'):continue
  try:
   page=fetch('https://www.fut.gg'+url)
   match=re.search(r'playerDef:\$R\[\d+\]=(?=\{)',page)
   if not match:continue
   definition=object_after(page,match.end())
   if definition.get('eaId')!=p['eaId'] or str(definition.get('game'))!='27':raise ValueError('Wrong rich item definition')
   attributes={k:v for k,v in definition.items() if k.startswith('attribute') and isinstance(v,(int,float))}
   if len(attributes)<30:raise ValueError('Incomplete attribute data')
   p['attributes']=attributes;args.details-=1
  except (ValueError,KeyError) as e:errors.append(str(e))
  time.sleep(.25)
 path.write_text(json.dumps({'updatedAt':datetime.now(timezone.utc).isoformat(),'items':items,'cursor':(cursor+30)%max(1,len(wanted)),'errors':errors},separators=(',',':'))+'\n')
 print('Builder catalogue:',len(es),'active Evolutions;',len(items),'verified items;',len(errors),'failed requests')
if __name__=='__main__':main()
