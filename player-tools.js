/* Shared player-page price status and links. Legacy item keys retain their URLs. */
(async()=>{
'use strict';
const script=document.currentScript,root=new URL('./',script.src),match=location.pathname.match(/-(\d+)\/?$/);if(!match)return;
const key=Number(match[1])>=1000000000?Number(match[1])-1000000000:Number(match[1]);let item=key;
try{const ids=await EzzcoinsMarket.fetchData('card-ids.json');item=Number(ids[key]||key);}catch{}
const box=document.getElementById('px');if(!box)return;
const controls=document.createElement('div');controls.className='ezz-profile-tools';const graph=document.createElement('button');graph.type='button';graph.textContent='Price graph';graph.dataset.priceGraph=item;graph.dataset.playerName=document.querySelector('h1')?.textContent||'Player';const builder=document.createElement('a');builder.href=new URL('tools.html#squad',root).href;builder.textContent='Squad Builder';const evo=document.createElement('a');evo.href=new URL('tools.html#evolutions',root).href;evo.textContent='Evolution Builder';controls.append(graph,builder,evo);box.parentElement.after(controls);
const status=document.createElement('p');status.className='ezz-profile-freshness';status.setAttribute('aria-live','polite');controls.after(status);let latest=null,checkedAt=null;
// When Ezzcoins last checked FUT.GG for new prices (the fast lane records every check on the `check` branch).
async function loadCheck(){try{const r=await fetch('https://raw.githubusercontent.com/SHAPELES-DGI/ezzcoin/check/check.json?t='+Math.floor(Date.now()/60000),{cache:'no-store',signal:AbortSignal.timeout(10000)});if(!r.ok)return;const t=Date.parse((await r.json()).checkedAt);if(Number.isFinite(t)&&t<=Date.now()+300000){checkedAt=t;apply();}}catch{}}
const checkText=()=>{if(!checkedAt)return'';const m=Math.max(0,Math.floor((Date.now()-checkedAt)/60000));return' · Ezzcoins '+(m>15?'last checked ':'checked ')+(m<1?'just now':m+' min ago');};
function apply(){const q=latest;if(!q||q.price==null)return;const f=EzzcoinsMarket.freshness(q.at);status.className='ezz-profile-freshness '+f.freshness;status.textContent='Console · '+q.src+' · '+new Date(q.at).toLocaleString()+' · '+(f.freshness==='fresh'?'Current quote':f.freshness==='delayed'?'Delayed quote':'Outdated quote')+' · '+f.ageMinutes+' min ago'+checkText();const old=box.querySelector('.price-updated');const text=f.freshness==='fresh'?'LIVE':f.freshness==='delayed'?'DELAYED':'OUTDATED';if(old&&old.textContent!==text){old.textContent=text;old.title=new Date(q.at).toLocaleString();}}
function update(data){latest=EzzcoinsMarket.lookup(data,item);if(!latest){status.textContent='Exact item '+item+' has no quote in the current feed.';return;}if(latest.price==null){status.textContent='No transferable market quote · '+(data.statusLabels?.[latest.status]||'Price unavailable');const old=box.querySelector('.price-updated');if(old)old.textContent='UNAVAILABLE';return;}apply();}
window.addEventListener('ezzcoins:quotes',e=>update(e.detail));new MutationObserver(apply).observe(box,{childList:true,subtree:true});setInterval(apply,60000);
loadCheck();setInterval(()=>{if(!document.hidden)loadCheck();},60000);
try{update(await EzzcoinsMarket.load());}catch{status.textContent='Price check failed. Refresh to retry; previously displayed prices may be outdated.';}
})();
