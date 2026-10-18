/* Ezzcoins player comparison: exact card identities and shared builder estimates. */
(function(root){
'use strict';
const C=root.EzzTools||(typeof require==='function'?require('./tools-core.js'):null);
function catalogue(data){
 const map=new Map(),roster=data['players.json'],ids=data['card-ids.json']||{},renders=data['card-renders.json']||{};
 for(const row of roster?.rows||[]){const p=Object.fromEntries(roster.cols.map((k,i)=>[k,row[i]]));p.stats=[1,2,3,4,5,6].map(i=>p['s'+i]);p.version=p.ovr>=75?'Gold':p.ovr>=65?'Silver':'Bronze';p.baseId=p.id;p.regular=data['playstyles.json']?.cards?.[p.id];map.set(+p.id,p);}
 for(const p of [...(data['newcards.json']?.cards||[]),...(data['legends.json']?.cards||[])]){
  const id=Number(ids[p.gid||p.fid]||p.eaId||p.gid);if(!Number.isSafeInteger(id)||id<=0||p.excluded)continue;
  // Never fill a special card's missing stats or PlayStyles from its base card.
  map.set(id,{...p,id,psp:p.psAt||p.ps?String(p.ps||'').split(',').filter(Boolean).map(v=>v.trim().replace(/\+$/,'')+'+').join(','):undefined,regular:p.psAt?p.pls:undefined});
 }
 for(const [id,item] of Object.entries(data['builder-items.json']?.items||{})){
  const p=map.get(+id)||{id:+id};
  map.set(+id,{...p,name:p.name||item.name,ovr:p.ovr||item.overall,pos:p.pos||item.position,alt:p.alt??(item.alternativePositions||[]).join(','),stats:p.stats?.length===6?p.stats:item.stats,sm:p.sm??item.skillMoves,wf:p.wf??item.weakFoot,club:p.club||item.club,nation:p.nation||item.nation,league:p.league||item.league,baseId:item.basePlayerEaId||p.baseId||+id,image:item.image,
   psp:p.psp??(Array.isArray(item.playStylePlusEaIds)?item.playStylePlusEaIds.map(n=>(C.PLAYSTYLES[n]||'PlayStyle '+n)+'+').join(','):undefined),
   regular:p.regular??(Array.isArray(item.playStyleEaIds)?item.playStyleEaIds.map(n=>C.PLAYSTYLES[n]||'PlayStyle '+n).join(', '):undefined)});
 }
 const market=data['market-cards.json'];if(market?.rows)for(const row of market.rows){const r=Object.fromEntries(market.cols.map((k,i)=>[k,row[i]])),p=map.get(+r.id);if(p&&!p.version)p.version=r.version;}
 return [...map.values()].filter(p=>p.id&&p.name&&p.pos&&p.ovr).map(p=>({...p,image:p.image||renders[p.id]?.url,version:p.version||(p.baseId===p.id?'Base':'Version unverified')}));
}
function score(p,pos,style,chem){return C.positions(p).includes(pos)?C.meta(p,pos,style,chem):null;}
function styles(p){return Object.keys(C.STYLES).filter(s=>p.pos==='GK'?C.GK_STYLES.includes(s):s==='None'||!C.GK_STYLES.includes(s));}
function verdict(cards,{pos,chem,budget,choices,quote}){
 const candidates=cards.map(p=>({p,meta:score(p,pos,choices[p.id]||'None',chem),q:quote(p.id)})).filter(x=>x.meta!=null&&x.q?.usable&&x.q.price>0&&(!budget||x.q.price<=budget));
 if(!candidates.length)return null;
 candidates.sort((a,b)=>b.meta-a.meta||a.q.price-b.q.price);
 const best=candidates[0],ties=candidates.filter(x=>x.meta===best.meta),value=candidates.slice().sort((a,b)=>a.q.price-b.q.price||b.meta-a.meta)[0];
 return {best,ties,value};
}
const API={catalogue,score,styles,verdict};root.EzzCompare=API;if(typeof module!=='undefined')module.exports=API;
})(typeof globalThis!=='undefined'?globalThis:this);
