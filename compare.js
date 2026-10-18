/* © 2026 Ezzcoins. Side-by-side player comparison. */
(async()=>{
'use strict';
const C=window.EzzTools,K=window.EzzCompare,M=window.EzzcoinsMarket,$=id=>document.getElementById(id);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const number=n=>Number.isFinite(n)?n.toLocaleString('en-US'):'—',norm=window.EzzcoinsSite.normalize;
const key='ezz.compare.v1';let pool=[],byId=new Map(),quotes=null,ids=[],choices={},priceFailed=false,catalogueReady=false;
const params=new URLSearchParams(location.search),queryIDs=(params.get('ids')||'').split(',').map(Number).filter(n=>Number.isSafeInteger(n)&&n>0).slice(0,4);
try{const saved=JSON.parse(localStorage.getItem(key));if(saved){ids=Array.isArray(saved.ids)?[...new Set(saved.ids.filter(n=>Number.isSafeInteger(n)&&n>0))].slice(0,4):[];choices=saved.choices&&typeof saved.choices==='object'?saved.choices:{};}}catch{}
if(queryIDs.length)ids=params.get('add')==='1'?[...new Set([...ids,...queryIDs])].slice(0,4):[...new Set(queryIDs)];
$('compare-position').innerHTML=Object.keys(C.W).map(pos=>`<option>${pos}</option>`).join('');$('compare-position').value=Object.hasOwn(C.W,params.get('pos'))?params.get('pos'):'ST';
if(['0','1','2','3'].includes(params.get('chem')))$('compare-chem').value=params.get('chem');
if(params.get('platform')==='pc')$('compare-platform').value='pc';
if(/^\d+$/.test(params.get('budget')||''))$('compare-budget').value=Math.min(15000000,Number(params.get('budget')));
try{const s=JSON.parse(params.get('styles'));if(s&&typeof s==='object'&&!Array.isArray(s))choices=s;}catch{}
const state=()=>({pos:$('compare-position').value,chem:Number($('compare-chem').value),platform:$('compare-platform').value,budget:Math.max(0,Number($('compare-budget').value)||0)});
const quote=id=>M.lookup(quotes,id,state().platform);
const say=text=>{$('compare-status').textContent=text;};
function persist(){try{localStorage.setItem(key,JSON.stringify({ids,choices}));}catch{}const s=state(),u=new URL(location.href);u.search='';if(ids.length)u.searchParams.set('ids',ids.join(','));u.searchParams.set('pos',s.pos);u.searchParams.set('chem',s.chem);u.searchParams.set('platform',s.platform);if(s.budget)u.searchParams.set('budget',s.budget);const used=Object.fromEntries(ids.filter(id=>choices[id]&&choices[id]!=='None').map(id=>[id,choices[id]]));if(Object.keys(used).length)u.searchParams.set('styles',JSON.stringify(used));history.replaceState(null,'',u);}
const image=p=>{try{const u=new URL(p.image);return u.protocol==='https:'&&u.hostname==='game-assets.fut.gg'?u.href:'';}catch{return '';}};
const art=p=>image(p)?`<img loading="lazy" src="${esc(image(p))}" alt="${esc(p.name+' '+p.version)} card">`:`<span class="card-placeholder" aria-label="Card artwork unavailable">${p.ovr}</span>`;
const chips=(value,plus=false)=>value==null?'<small>Unverified</small>':value?String(value).split(',').map(v=>`<span class="ps-chip${plus?' plus':''}">${esc(v.trim())}</span>`).join(''):'<small>None</small>';
function search(){
 const text=norm($('compare-search').value).trim(),terms=text.split(/\s+/).filter(Boolean);
 if(!text){$('search-results').innerHTML='';return;}
 const results=pool.filter(p=>terms.every(t=>p.search.includes(t))).sort((a,b)=>Number(norm(b.name)===text)-Number(norm(a.name)===text)||b.ovr-a.ovr||a.name.localeCompare(b.name)).slice(0,24);
 $('search-results').innerHTML=results.length?results.map(p=>`<button class="compare-result" type="button" data-add="${p.id}"${ids.includes(p.id)||ids.length===4?' disabled':''}>${image(p)?art(p):`<span>${p.ovr}</span>`}<span><b>${esc(p.name)}</b><small>${p.ovr} · ${esc(p.pos)} · ${esc(p.version)}</small><small>${esc(p.club||p.nation)} · Item ${p.id}</small></span><span class="add">${ids.includes(p.id)?'Added':ids.length===4?'Full':'+ Add'}</span></button>`).join(''):'<p class="empty">No cards match. Try a player name or card version.</p>';
}
function price(p){const q=quote(p.id);if(!q?.price)return `<span>${esc(({1:'SBC · untradeable',2:'Objective · untradeable',3:'Not on the market',4:'Reward · untradeable'})[q?.status]||'No verified quote')}</span>`;
 const d=Date.parse(q.at),at=Number.isFinite(d)?new Date(d).toLocaleString():'Unknown source time';return `<b>${number(q.price)} coins</b><small>${esc(priceFailed?'Last check failed · saved quote':q.freshness)}${q.ageMinutes==null?'':' · '+q.ageMinutes+' min ago'}<br>${esc(q.src)} · ${esc(at)}</small>`;}
function render(){
 const cards=ids.map(id=>byId.get(id)).filter(Boolean),s=state();$('selection-count').textContent=cards.length+' / 4';
 $('clear-comparison').disabled=!ids.length;$('share-comparison').disabled=!ids.length;
 if(!cards.length){$('comparison').innerHTML='<p class="empty">Search above to add your first player.</p>';$('compare-verdict').innerHTML='<h2>Choose your contenders</h2><p>Add at least two cards to compare them.</p>';search();return;}
 const values=cards.map(p=>K.score(p,s.pos,choices[p.id]||'None',s.chem));
 function row(label,fn,numeric=false){const nums=numeric?cards.map((p,i)=>fn(p,i)).filter(Number.isFinite):[],max=nums.length?Math.max(...nums):null;return `<tr><th scope="row">${esc(label)}</th>${cards.map((p,i)=>{const value=fn(p,i);return `<td${numeric&&Number.isFinite(value)&&value===max?' class="best"':''}>${numeric?(value==null?'—':esc(value)):value}</td>`;}).join('')}</tr>`;}
 const sameType=cards.every(p=>(p.pos==='GK')===(cards[0].pos==='GK'));
 const labels=cards[0].pos==='GK'?['Diving','Handling','Kicking','Reflexes','Speed','Positioning']:['Pace','Shooting','Passing','Dribbling','Defending','Physical'];
 const faceRows=sameType?labels.map((label,i)=>row(label,p=>Number.isFinite(p.stats?.[i])?p.stats[i]:null,true)).join(''):row('Base face stats',p=>(p.pos==='GK'?['DIV','HAN','KIC','REF','SPD','POS']:['PAC','SHO','PAS','DRI','DEF','PHY']).map((label,i)=>esc(label)+' '+esc(p.stats?.[i]??'—')).join(' · '));
 const labelWidth=matchMedia('(max-width:760px)').matches?88:150,cardWidth=matchMedia('(max-width:760px)').matches?142:220;
 $('comparison').innerHTML=`<table class="comparison-table" style="min-width:${labelWidth+cardWidth*cards.length}px"><caption class="sr-only">Exact player card comparison at ${s.chem} chemistry</caption><colgroup><col style="width:${labelWidth}px">${cards.map(()=>'<col>').join('')}</colgroup><thead><tr><th scope="col">${cards.length} card${cards.length===1?'':'s'}<small>${esc(s.platform)} · ${s.chem} chemistry</small></th>${cards.map(p=>`<th scope="col">${art(p)}<h2>${esc(p.name)}</h2><small>${p.ovr} OVR · ${esc(p.version)}<br>Item ${p.id}</small><button class="remove-card" data-remove="${p.id}" aria-label="Remove ${esc(p.name+' '+p.version)}">Remove</button></th>`).join('')}</tr></thead><tbody>`+
 row('Position fit',p=>C.positions(p).includes(s.pos)?`<b class="up">Eligible at ${esc(s.pos)}</b>`:`<span class="down">Cannot play ${esc(s.pos)}</span>`)+
 row(s.pos+' meta',(p,i)=>values[i],true)+row('Chemistry style',p=>`<label>Style for ${esc(p.name+' '+p.version)}<select data-style="${p.id}">${K.styles(p).map(style=>`<option${(choices[p.id]||'None')===style?' selected':''}>${esc(style)}</option>`).join('')}</select></label>`)+
 row('Market price',price)+row('Budget fit',p=>{const q=quote(p.id);return !s.budget?'No budget set':!q?.price?'Unknown':q.price<=s.budget?'<span class="up">Within budget</span>':'<span class="down">'+number(q.price-s.budget)+' over budget</span>';})+
 row('Overall',p=>p.ovr,true)+faceRows+row('Skill moves',p=>p.sm??null,true)+row('Weak foot',p=>p.wf??null,true)+row('PlayStyles+',p=>chips(p.psp,true))+row('PlayStyles',p=>chips(p.regular))+
 row('All position meta',p=>`<span class="meta-positions">${C.positions(p).map(pos=>`${esc(pos)} <b>${K.score(p,pos,choices[p.id]||'None',s.chem)??'—'}</b>`).join(' · ')}</span>`)+row('Club',p=>esc(p.club||'—'))+row('League',p=>esc(p.league||'—'))+row('Nation',p=>esc(p.nation||'—'))+'</tbody></table>';
 if(cards.length<2)$('compare-verdict').innerHTML='<h2>One more contender</h2><p>Add another exact card version to compare stats and value.</p>';
 else{
 const result=priceFailed?null:K.verdict(cards,{...s,choices,quote});
 if(!result)$('compare-verdict').innerHTML='<h2>No price-based pick available</h2><p>A recommendation needs an eligible card with verified stats and a fresh price'+(s.budget?' within your budget':'')+'. Compare the available stats below, adjust the position or budget, or refresh prices.</p>';
 else{const {best,ties,value}=result;const equal=ties.length>1;
 $('compare-verdict').innerHTML=`<h2>${equal?'Joint highest meta':'Highest meta'}${s.budget?' within budget':''}: ${esc(best.p.name)}</h2><p>${best.meta} ${esc(s.pos)} meta · ${number(best.q.price)} coins · ${esc(best.p.version)}.${equal?' '+ties.length+' selected cards share this meta rating; this is the cheapest of them.':''}</p><p><b>Lowest eligible cost:</b> ${esc(value.p.name)} (${esc(value.p.version)}) · ${number(value.q.price)} coins · ${value.meta} meta. ${best.p.id!==value.p.id?`The highest-meta option costs ${number(best.q.price-value.q.price)} more for ${best.meta-value.meta} extra meta points.`:'This card also has the lowest eligible cost.'}</p><small>Among your selected cards, using eligible positions and fresh ${esc(s.platform)} quotes at ${s.chem} chemistry. This is a comparison of the available numbers, not a guarantee of in-game performance.</small>`;
 }
 }
 search();
}
$('compare-search').addEventListener('input',search);
$('search-results').onclick=e=>{const b=e.target.closest('[data-add]');if(!b||b.disabled)return;const id=+b.dataset.add;if(ids.length>=4||ids.includes(id))return;ids.push(id);if(ids.length===1&&!params.has('pos'))$('compare-position').value=byId.get(id).pos;persist();render();say('Added '+byId.get(id).name+'.');};
$('comparison').onclick=e=>{const b=e.target.closest('[data-remove]');if(!b)return;ids=ids.filter(id=>id!==+b.dataset.remove);persist();render();};
$('comparison').onchange=e=>{const id=+e.target.dataset.style,p=byId.get(id);if(p&&K.styles(p).includes(e.target.value)){choices[id]=e.target.value;persist();render();}};
for(const id of ['compare-position','compare-chem','compare-platform','compare-budget'])$(id).addEventListener('input',()=>{if(!$(id).checkValidity())return;persist();render();});
$('clear-comparison').onclick=()=>{ids=[];choices={};persist();render();say('Comparison cleared.');};
$('share-comparison').onclick=async()=>{persist();try{await navigator.clipboard.writeText(location.href);say('Comparison link copied, including cards, styles and settings.');}catch{say('Copy the URL from your address bar to share this comparison.');}};
async function refresh(){const b=$('refresh-comparison');b.disabled=true;priceFailed=false;try{quotes=await M.load(true);say(priceFailed?'Price check failed. Previous quotes remain visible.':'Newest available prices loaded.');}catch{priceFailed=true;say('Prices could not load. You can still compare player data.');}finally{b.disabled=false;render();}}
$('refresh-comparison').onclick=refresh;
window.addEventListener('ezzcoins:quotes',e=>{priceFailed=false;quotes=e.detail;if(catalogueReady)render();});
window.addEventListener('ezzcoins:quote-error',()=>{priceFailed=true;say('Latest price check failed. Saved quotes may be outdated.');if(catalogueReady)render();});
async function loadCatalogue(){
 $('retry-catalogue').hidden=true;say('Loading player catalogue…');
 const names=['players.json','newcards.json','legends.json','card-ids.json','card-renders.json','builder-items.json','market-cards.json','playstyles.json'];
 const results=await Promise.allSettled(names.map(n=>M.fetchData(n))),data=Object.fromEntries(names.map((n,i)=>[n,results[i].status==='fulfilled'?results[i].value:null]));
 if(!data['players.json']?.rows?.length){say('Player catalogue could not load. Retry to load your saved comparison.');$('retry-catalogue').hidden=false;return;}
 pool=K.catalogue(data);for(const p of pool)p.search=norm([p.name,p.full,p.version,p.club,p.nation,p.id].join(' '));byId=new Map(pool.map(p=>[+p.id,p]));
 const missing=ids.filter(id=>!byId.has(id));ids=ids.filter(id=>byId.has(id));for(const p of pool)if(!K.styles(p).includes(choices[p.id]))delete choices[p.id];
 catalogueReady=true;$('compare-search').disabled=false;if(!params.has('pos')&&ids.length)$('compare-position').value=byId.get(ids[0]).pos;persist();render();
 const partial=names.filter(n=>!data[n]);say(missing.length?'Some selected cards are no longer available in the catalogue.':partial.length?'Some card details could not load. Missing information is marked unverified.':pool.length.toLocaleString()+' exact cards ready. Search above to add players.');
 await refresh();
}
$('retry-catalogue').onclick=loadCatalogue;
await loadCatalogue();
matchMedia('(max-width:760px)').addEventListener('change',()=>{if(catalogueReady)render();});
setInterval(()=>{if(catalogueReady)render();},60000);
setInterval(()=>{if(catalogueReady&&!document.hidden)refresh();},300000);
})();
