/* Ezzcoins builders. Pure calculations shared by the page and solver worker. */
(function(root){
'use strict';
const W={ST:[.30,.30,.05,.22,0,.13],CF:[.28,.26,.10,.28,0,.08],LW:[.33,.20,.12,.30,0,.05],RW:[.33,.20,.12,.30,0,.05],LM:[.32,.15,.18,.28,.02,.05],RM:[.32,.15,.18,.28,.02,.05],CAM:[.22,.20,.25,.30,0,.03],CM:[.18,.10,.28,.22,.10,.12],CDM:[.18,0,.20,.10,.30,.22],CB:[.30,0,.07,.03,.40,.20],LB:[.33,0,.15,.14,.26,.12],RB:[.33,0,.15,.14,.26,.12],LWB:[.33,0,.16,.16,.23,.12],RWB:[.33,0,.16,.16,.23,.12],GK:[.27,.15,.03,.30,.05,.20]};
const OFF={ST:2,CF:1.5,LW:-1.3,RW:-1.3,LM:.1,RM:.1,CAM:1,CM:4,CDM:5.1,CB:5.9,LB:2.8,RB:2.8,LWB:2.8,RWB:2.8,GK:.2};
const STARS={CM:[.6,.8],CDM:[.3,.5],CB:[0,.4],LB:[.3,.5],RB:[.3,.5],LWB:[.4,.5],RWB:[.4,.5],GK:[0,0]};
const STRONG=new Set(['Quick Step+','Rapid+','Finesse Shot+','Technical+','Low Driven Shot+','Power Shot+','Trickster+','Intercept+','Anticipate+','Jockey+','Bruiser+','Footwork+','Far Reach+','Deflector+','Rush Out+','1v1 Close Down+']);
const MINOR=new Set(['Dead Ball+','Long Throw+','Far Throw+']);
const STYLES={None:[0,0,0,0,0,0],Basic:[1.65,.9,2.25,2.7,2.1,1.5],Hunter:[6,2.85,0,0,0,0],Shadow:[6,0,0,0,3.9,0],Engine:[3,0,3.6,3.3,0,0],Anchor:[3,0,0,0,4.2,3.9],Finisher:[0,5.25,0,4.95,0,0],Catalyst:[6,0,5.1,0,0,0],Hawk:[3,4.05,0,0,0,3],Glove:[6,9,0,0,0,3],Cat:[0,0,0,6,1.8,9]};
const POS={0:'GK',3:'RB',5:'CB',7:'LB',10:'CDM',12:'RM',14:'CM',16:'LM',18:'CAM',23:'RW',25:'ST',27:'LW'};
// FC 27 Ultimate Team formations, drawn on the pitch from attack to goal. Each slot is "POSITION" + the column it
// starts in on a 10-column pitch; every slot spans 2 columns, so all boxes are the same size (1 3 5 7 9 = five across).
// Since FC 25 there are no CF, LWB or RWB slots: five-at-the-back uses LB/RB and the old CF slots are CAMs.
// Slot order (top row first, left to right) is what saved squads store, so existing formations keep their order.
const B4='LB2 CB4 CB6 RB8',B3='CB3 CB5 CB7',B5='LB1 CB3 CB5 CB7 RB9',M4='LM1 CM4 CM6 RM9',F3='LW1 ST5 RW9',S2='ST3 ST7';
const LAYOUTS={
 '4-3-3':[F3,'CM3 CM5 CM7',B4],'4-3-3 (2)':[F3,'CM3 CM7','CDM5',B4],'4-3-3 (3)':[F3,'CM5','CDM4 CDM6',B4],'4-3-3 (4)':[F3,'CAM5','CM3 CM7',B4],
 '4-4-2':[S2,M4,B4],'4-4-2 (2)':[S2,'LM1 CDM4 CDM6 RM9',B4],'4-4-1-1 (2)':['ST5','CAM5',M4,B4],
 '4-2-3-1':['ST5','CAM2 CAM5 CAM8','CDM4 CDM6',B4],'4-2-3-1 (2)':['ST5','LM1 CAM5 RM9','CDM4 CDM6',B4],
 '4-1-2-1-2':[S2,'CAM5','LM1 RM9','CDM5',B4],'4-1-2-1-2 (2)':[S2,'CAM5','CM3 CM7','CDM5',B4],
 '4-1-3-2':[S2,'LM1 CM5 RM9','CDM5',B4],'4-1-4-1':['ST5',M4,'CDM5',B4],'4-2-1-3':[F3,'CAM5','CDM4 CDM6',B4],
 '4-2-2-2':[S2,'CAM2 CAM8','CDM4 CDM6',B4],'4-2-4':['LW1 ST4 ST6 RW9','CM4 CM6',B4],'4-3-1-2':[S2,'CAM5','CM3 CM5 CM7',B4],
 '4-3-2-1':['ST5','CAM3 CAM7','CM3 CM5 CM7',B4],'4-5-1':['ST5','CAM3 CAM7','LM1 CM5 RM9',B4],'4-5-1 (2)':['ST5','LM1 CM3 CM5 CM7 RM9',B4],
 '3-5-2':[S2,'CAM5','LM1 CDM4 CDM6 RM9',B3],'3-1-4-2':[S2,M4,'CDM5',B3],'3-4-1-2':[S2,'CAM5',M4,B3],'3-4-2-1':['ST5','CAM3 CAM7',M4,B3],'3-4-3':[F3,M4,B3],
 '5-2-1-2':[S2,'CAM5','CM4 CM6',B5],'5-2-3':[F3,'CM4 CM6',B5],'5-3-2':[S2,'CM3 CM7','CDM5',B5],'5-4-1':['ST5',M4,B5]
};
const ROWS=Object.fromEntries(Object.entries(LAYOUTS).map(([f,rows])=>[f,[...rows,'GK5'].map(r=>r.split(' ').map(t=>({pos:t.replace(/\d+$/,''),col:Number(t.match(/\d+$/)[0])})))]));
const FORMATIONS=Object.fromEntries(Object.entries(ROWS).map(([f,rows])=>[f,rows.flat().map(s=>s.pos)]));
const positions=p=>[...new Set([p.pos,...String(p.alt||'').split(',')].map(v=>v.trim()).filter(v=>W[v]))];
function meta(p,pos=p.pos,style='None',chem=3){
 if(!W[pos]||!Array.isArray(p.stats)||p.stats.length!==6||p.stats.some(x=>!Number.isFinite(x)))return null;
 const s=p.stats.map((v,i)=>Math.min(99,v+(STYLES[style]?.[i]||0)*chem/3));
 let n=s.reduce((a,v,i)=>a+v*W[pos][i],0)+OFF[pos];
 if(pos!=='GK'){if(s[0]<70&&W[pos][0]>=.25)n-=(70-s[0])*.15;const [sm,wf]=STARS[pos]||[1,1];n+=sm*((p.sm||3)-3)+wf*((p.wf||3)-3);}
 for(const ps of String(p.psp||'').split(',').map(v=>v.trim()).filter(Boolean))n+=MINOR.has(ps)?.5:STRONG.has(ps)?2:1;
 return Math.max(1,Math.min(99,Math.floor(n+.5)));
}
const base=p=>p.baseId||p.id;
function chemistry(squad,slots,manager={}){
 const active=squad.map((p,i)=>p&&positions(p).includes(slots[i])?p:null);
 const clubs={},nations={},leagues={};const inc=(o,k,v=1)=>{if(k)o[k]=(o[k]||0)+v;};
 for(const p of active){if(!p)continue;inc(clubs,p.club,1+(p.extraClubChemistry||0));inc(nations,p.nation,1+(p.extraNationChemistry||0));if(!p.isIcon)inc(leagues,p.league,1+(p.extraLeagueChemistry||0));}
 const icons=active.filter(p=>p?.isIcon).length;
 const threshold=(n,a)=>a.filter(v=>n>=v).length;
 // FC 27: a manager does not count towards link thresholds; an in-position starter sharing the manager's nation or league gets one flat point (max one, total still capped at 3).
 const boss=p=>(manager.nation&&p.nation===manager.nation)||(manager.league&&p.league===manager.league)?1:0;
 const points=active.map(p=>!p?0:p.isIcon||p.isHero||p.isFullChemistry?3:Math.min(3,threshold(clubs[p.club]||0,[2,4,7])+threshold((nations[p.nation]||0)+active.filter(v=>v?.extraSquadNationChemistry&&v.nation!==p.nation).length,[2,5,8])+threshold((leagues[p.league]||0)+icons+active.filter(v=>v?.extraSquadLeagueChemistry&&v.league!==p.league).length,[3,5,8])+boss(p)));
 return {points,total:points.reduce((a,b)=>a+b,0),clubs,nations,leagues};
}
function squadRating(players){if(!players.length)return 0;const avg=players.reduce((a,p)=>a+p.ovr,0)/players.length;return Math.floor((players.reduce((a,p)=>a+p.ovr+Math.max(0,p.ovr-avg),0)/players.length)+1e-9);}
function autoSquad(pool,slots,budget,locked=[]){
 let selected=Array(slots.length).fill(null);const used=new Set();let remaining=budget;
 locked.forEach((p,i)=>{if(p){selected[i]=p;used.add(base(p));remaining-=p.price||0;}});
 if(remaining<0)return {error:'Locked players exceed the budget.'};
 // Fill the hardest positions first with cheap valid items, then spend remaining coins on meta improvements.
 const candidates=slots.map(pos=>pool.filter(p=>p.price>0&&p.usable&&positions(p).includes(pos)&&meta(p,pos)!=null).sort((a,b)=>a.price-b.price||meta(b,pos)-meta(a,pos)));
 const order=slots.map((_,i)=>i).filter(i=>!selected[i]).sort((a,b)=>candidates[a].length-candidates[b].length);
 for(const i of order){const p=candidates[i].find(v=>!used.has(base(v))&&v.price<=remaining);if(!p)return {error:'No complete squad found within this budget using fresh quotes. Increase the budget or change the formation.'};selected[i]=p;used.add(base(p));remaining-=p.price;}
 for(let pass=0;pass<44;pass++){
  let best=null;
  for(let i=0;i<slots.length;i++){
   if(locked[i])continue;
   const current=selected[i],old=meta(current,slots[i]);
   for(const p of candidates[i]){
    if((used.has(base(p))&&base(p)!==base(current))||p.price-current.price>remaining)continue;
    const gain=meta(p,slots[i])-old;if(gain<=0)continue;
    const score=gain/(1+Math.max(0,p.price-current.price)/1000);
    if(!best||score>best.score)best={i,p,score};
   }
  }
  if(!best)break;const old=selected[best.i];used.delete(base(old));used.add(base(best.p));remaining+=old.price-best.p.price;selected[best.i]=best.p;
 }
 return {players:selected,cost:budget-remaining};
}
function requirementRules(text){
 const rules=[],unsupported=[];
 for(const part of String(text||'').split(';').map(v=>v.trim()).filter(Boolean)){
  let m;
  if((m=part.match(/^(?:Team rating|Squad Rating): Min\. (\d+)$/i)))rules.push({kind:'rating',op:'min',value:+m[1]});
  else if((m=part.match(/^Chemistry: Min\. (\d+)$/i)))rules.push({kind:'chem',op:'min',value:+m[1]});
  else if((m=part.match(/^Rating: (Min\.|Max\.) (\d+)$/i)))rules.push({kind:'playerRating',op:m[1]==='Min.'?'min':'max',value:+m[2]});
  else if((m=part.match(/^Rating: (\d+) to (\d+)$/i)))rules.push({kind:'playerRating',op:'range',value:+m[1],max:+m[2]});
  else if((m=part.match(/^Quality: (?:Min\. )?(Gold|Silver|Bronze)( only)?$/i)))rules.push({kind:'quality',value:m[1].toLowerCase(),op:part.includes('Min.')?'min':'exact'});
  else if((m=part.match(/^(Leagues|Nations|Clubs): (Exactly|Min\.|Max\.) (\d+)$/i)))rules.push({kind:m[1].toLowerCase().replace(/s$/,''),op:m[2]==='Exactly'?'exact':m[2]==='Min.'?'min':'max',value:+m[3]});
  else if((m=part.match(/^Same (league|nation|club): (Max\.|Min\.) (\d+) players$/i)))rules.push({kind:'same'+m[1],op:m[2]==='Max.'?'max':'min',value:+m[3]});
  else if((m=part.match(/^(League|Nation|Club): (.+)$/i)))rules.push({kind:'all'+m[1].toLowerCase(),value:m[2],op:'exact'});
  else if((m=part.match(/^Players in (?:the )?Squad: (\d+)$/i)))rules.push({kind:'count',value:+m[1],op:'exact'});
  else unsupported.push(part);
 }
 return {rules,unsupported};
}
function quality(p){return p.ovr>=75?'gold':p.ovr>=65?'silver':'bronze';}
function individualOK(p,rules){return rules.every(r=>r.kind==='playerRating'?(r.op==='min'?p.ovr>=r.value:r.op==='max'?p.ovr<=r.value:p.ovr>=r.value&&p.ovr<=r.max):r.kind==='quality'?(r.op==='min'?p.ovr>=(r.value==='gold'?75:r.value==='silver'?65:45):quality(p)===r.value):r.kind.startsWith('all')?p[r.kind.slice(3)]===r.value:true);}
function validateSbc(players,parsed,slots=FORMATIONS['4-4-2']){
 const rows=parsed.rules.map(r=>{
  let value;
  if(r.kind==='rating')value=squadRating(players);
  else if(r.kind==='chem')value=chemistry(players,slots).total;
  else if(r.kind==='count')value=players.length;
  else if(['league','nation','club'].includes(r.kind))value=new Set(players.map(p=>p[r.kind])).size;
  else if(r.kind.startsWith('same')){const k=r.kind.slice(4),counts={};for(const p of players)counts[p[k]]=(counts[p[k]]||0)+1;value=Math.max(0,...Object.values(counts));}
  else return {rule:r,pass:players.every(p=>individualOK(p,[r]))};
  return {rule:r,value,pass:r.op==='min'?value>=r.value:r.op==='max'?value<=r.value:value===r.value};
 });
 return {valid:players.length===11&&new Set(players.map(base)).size===11&&!parsed.unsupported.length&&rows.every(r=>r.pass),rows,unsupported:parsed.unsupported};
}
function solveScore(pool,target,parsed){
 if(!Number.isSafeInteger(target)||target<=0)return {error:'Missing Item Score target.'};
 if(parsed.unsupported.length)return {error:'This challenge has requirements the solver cannot verify: '+parsed.unsupported.join('; ')};
 const candidates=pool.filter(p=>p.price>0&&p.usable&&Number.isSafeInteger(p.gradingScore)&&p.gradingScore>0&&individualOK(p,parsed.rules));
 if(!candidates.length)return {error:'No eligible items with verified Item Scores and fresh prices.'};
 const best=new Map();for(const p of candidates)if(!best.has(p.gradingScore)||p.price<best.get(p.gradingScore).price)best.set(p.gradingScore,p);
 const items=[...best.values()];const gcd=(a,b)=>b?gcd(b,a%b):a;const unit=items.reduce((n,p)=>gcd(n,p.gradingScore),0);const goal=Math.ceil(target/unit),max=Math.min(...items.filter(p=>p.gradingScore>=target).map(p=>p.gradingScore/unit),goal+Math.max(...items.map(p=>p.gradingScore/unit))-1);
 if(max>250000)return {error:'This score target exceeds the current exact solver limit. Open the verified source solution.'};
 const cost=new Float64Array(max+1);cost.fill(Infinity);cost[0]=0;const prev=new Int32Array(max+1);prev.fill(-1);
 for(let s=1;s<=max;s++)for(let i=0;i<items.length;i++){const v=items[i].gradingScore/unit;if(v<=s&&cost[s-v]+items[i].price<cost[s]){cost[s]=cost[s-v]+items[i].price;prev[s]=i;}}
 let end=goal;for(let s=goal+1;s<=max;s++)if(cost[s]<cost[end])end=s;
 if(!Number.isFinite(cost[end]))return {error:'No solution found.'};
 const counts=new Map();let at=end;while(at>0){const i=prev[at];if(i<0)return {error:'No complete solution.'};counts.set(items[i].id,(counts.get(items[i].id)||0)+1);at-=items[i].gradingScore/unit;}
 return {players:[...counts].map(([id,quantity])=>({...items.find(p=>p.id===id),quantity})),cost:cost[end],score:end*unit,optimalWithinPool:true};
}
function solvePuzzle(pool,parsed,slots=FORMATIONS['4-4-2']){
 if(parsed.unsupported.length)return {error:'Unverified requirements: '+parsed.unsupported.join('; ')};
 const candidates=pool.filter(p=>p.price>0&&p.usable&&individualOK(p,parsed.rules)).sort((a,b)=>a.price-b.price);
 let best=null;const usesChem=parsed.rules.some(r=>r.kind==='chem');
 const tryPool=arr=>{
  let squad=[],used=new Set();
  for(let i=0;i<11;i++){const p=arr.find(p=>!used.has(base(p))&&(!usesChem||positions(p).includes(slots[i])));if(!p)return;used.add(base(p));squad.push(p);}
  // Rating upgrades retain unique base players and position eligibility.
  for(let n=0;n<120&&!validateSbc(squad,parsed,slots).valid;n++){
   const current=squadRating(squad),need=parsed.rules.find(r=>r.kind==='rating')?.value||0;if(current>=need)break;
   let swap=null;
   for(let i=0;i<11;i++)for(const p of arr){if(used.has(base(p))||p.ovr<=squad[i].ovr||(usesChem&&!positions(p).includes(slots[i])))continue;const score=(p.price-squad[i].price)/Math.max(1,p.ovr-squad[i].ovr);if(!swap||score<swap.score)swap={i,p,score};}
   if(!swap)break;used.delete(base(squad[swap.i]));squad[swap.i]=swap.p;used.add(base(swap.p));
  }
  const validation=validateSbc(squad,parsed,slots);if(!validation.valid)return;const cost=squad.reduce((n,p)=>n+p.price,0);if(!best||cost<best.cost)best={players:squad,cost,validation,optimalWithinPool:false};
 };
 tryPool(candidates);
 const groups=['league','nation','club'];
 for(const key of groups){const values=[...new Set(candidates.map(p=>p[key]))].filter(Boolean);for(const val of values.slice(0,70)){const linked=candidates.filter(p=>p[key]===val);tryPool(linked);tryPool([...linked,...candidates.filter(p=>p[key]!==val)]);}}
 return best||{error:'No fully valid squad found. The solver will not show an invalid squad as a solution. Use the source solution for this challenge.'};
}
function eligibility(card,evo){
 const r=evo.requirements||{},reasons=[];if(evo.endTime&&Date.parse(evo.endTime)<=Date.now())reasons.push('Expired');
 for(const [k,v] of Object.entries(r)){
  if(v==null||v===false||['game','readableSchemas','positionsSearchMode','leagueNationSearchMode','playstylesSearchMode','excludeIsNotInSearch'].includes(k))continue;
  const nums={minOverall:card.ovr,maxOverall:card.ovr,maxFacePace:card.stats?.[0],maxPlaystyles:card.playStyleEaIds&&card.playStylePlusEaIds?new Set([...card.playStyleEaIds,...card.playStylePlusEaIds]).size:null,maxPlaystylesPlus:card.playStylePlusEaIds?.length,minBirthDate:card.birthDate,totalNumberOfPositions:positions(card).length};
  if(Object.hasOwn(nums,k)){if(nums[k]==null)reasons.push('Missing '+k+' data');else if(k.startsWith('min')?nums[k]<v:k==='totalNumberOfPositions'?nums[k]>v:nums[k]>v)reasons.push(k+': '+v);}
  else if(k==='positions'&&!positions(card).some(p=>v.map(i=>POS[i]).includes(p)))reasons.push('Position requirement');
  else if(k==='excludedPositions'&&positions(card).some(p=>v.map(i=>POS[i]).includes(p)))reasons.push('Excluded position');
  else if(k==='rarities'&&(card.rarityEaId==null||!v.includes(card.rarityEaId)))reasons.push('Rarity requirement');
  else if(k==='excludedRarities'&&(card.rarityEaId==null||v.includes(card.rarityEaId)))reasons.push('Excluded or unknown rarity');
  else if(!['positions','excludedPositions','rarities','excludedRarities'].includes(k))reasons.push('Unsupported rule: '+k);
 }
 return {eligible:!reasons.length,reasons};
}
const FACE_GROUPS=[
 [['Acceleration',.45],['SprintSpeed',.55]],
 [['Positioning',.05],['Finishing',.45],['ShotPower',.2],['LongShots',.2],['Volleys',.05],['Penalties',.05]],
 [['Vision',.2],['Crossing',.2],['FkAccuracy',.05],['ShortPassing',.35],['LongPassing',.15],['Curve',.05]],
 [['Agility',.1],['Balance',.05],['Reactions',.05],['BallControl',.3],['Dribbling',.45],['Composure',.05]],
 [['Interceptions',.2],['HeadingAccuracy',.1],['DefensiveAwareness',.3],['StandingTackle',.3],['SlidingTackle',.1]],
 [['Jumping',.05],['Stamina',.25],['Strength',.5],['Aggression',.2]]
];
const GK_GROUPS=[[['GkDiving',1]],[['GkHandling',1]],[['GkKicking',1]],[['GkReflexes',1]],[['Acceleration',.6],['SprintSpeed',.4]],[['GkPositioning',1]]];
const camel=key=>key.split('_').map(s=>s[0].toUpperCase()+s.slice(1)).join('');
function evolve(card,evo,choices={}){
 const check=eligibility(card,evo);if(!check.eligible)return {error:check.reasons.join(', ')};
 const repeats=(card.evolutionIds||[]).filter(id=>id===evo.id).length;
 if(repeats>=(evo.repeatabilityCount||1))return {error:'This Evolution has already been used on this path.'};
 for(const level of evo.levels||[])if(level.upgradeOptions?.length&&!level.upgradeOptions.some(o=>o.idx===+choices[level.idx]))return {error:'Choose an upgrade option for level '+level.idx+'.'};
 const useExample=card.id===evo.example?.before?.eaId&&!card.evolutionIds?.length&&!evo.hasUpgradeChoices;
 let out={...card,stats:card.stats?.slice(),attributes:{...card.attributes},playStyleEaIds:[...(card.playStyleEaIds||[])],playStylePlusEaIds:[...(card.playStylePlusEaIds||[])],evolutionIds:[...(card.evolutionIds||[]),evo.id]};
 const groups=card.pos==='GK'?GK_GROUPS:FACE_GROUPS,faces=card.pos==='GK'?['gk_face_diving','gk_face_handling','gk_face_kicking','gk_face_reflexes','gk_face_speed','gk_face_positioning']:['face_pace','face_shooting','face_passing','face_dribbling','face_defending','face_physicality'];
 const touched=new Set(),missing=[],upgradeLabels=[];
 for(const level of evo.levels||[]){
  const option=level.upgradeOptions?.find(o=>o.idx===+choices[level.idx]);
  for(const u of [...(level.upgrades||[]),...(option?.upgrades||[])]){
   const cap=(old,add)=>Math.max(old,Math.min(u.maxValue??99,old+add));
   if(u.upgrade==='overall')out.ovr=cap(out.ovr,u.value);
   else if(u.upgrade==='skill_moves')out.sm=cap(out.sm||1,u.value);
   else if(u.upgrade==='weak_foot')out.wf=cap(out.wf||1,u.value);
   else if(u.upgrade==='play_style'){if(!out.playStyleEaIds.includes(u.value)&&out.playStyleEaIds.length<(u.maxValue??99))out.playStyleEaIds.push(u.value);}
   else if(u.upgrade==='rarity_id')out.rarityEaId=u.value;
   else if(faces.includes(u.upgrade)){
    const i=faces.indexOf(u.upgrade),delta=cap(out.stats[i],u.value)-out.stats[i];out.stats[i]+=delta;
    if(delta){for(const [name] of groups[i]){const key='attribute'+name;if(out.attributes[key]==null)missing.push(key);else out.attributes[key]=Math.min(99,out.attributes[key]+delta);}touched.add(i);}
   } else if(u.upgrade.startsWith('attribute_')){
    const key=camel(u.upgrade).replace(/^Attribute/,'attribute');
    if(out.attributes[key]==null)missing.push(key);else out.attributes[key]=cap(out.attributes[key],u.value);
    groups.forEach((group,i)=>{if(group.some(([name])=>'attribute'+name===key))touched.add(i);});
   } else if(!['role_plus','role_plus_plus'].includes(u.upgrade))missing.push(u.upgrade);
  }
  upgradeLabels.push(...(level.totalUpgradesText||[]),...(option?.totalUpgradesText||[]));
  // Recompute face stats before the next level's caps are applied.
  for(const i of touched){const group=groups[i];if(group.some(([name])=>out.attributes['attribute'+name]==null)){missing.push('Face-stat attributes');continue;}out.stats[i]=Math.min(99,Math.round(group.reduce((n,[name,w])=>n+out.attributes['attribute'+name]*w,0)+1e-9));}
 }
 if(useExample){const a=evo.example.after;return {card:{...out,ovr:a.overall,stats:a.stats,pos:a.position,alt:(a.alternativePositions||[]).join(','),sm:a.skillMoves,wf:a.weakFoot,playStyleEaIds:a.playStyleEaIds,playStylePlusEaIds:a.playStylePlusEaIds,rarityEaId:a.rarityEaId,sourcePreview:true},verified:true};}
 if(missing.length)return {error:'Final stats need more detailed metadata for this card. Select the verified example or open the source planner.',upgrades:upgradeLabels};
 return {card:out,verified:false,upgrades:upgradeLabels};
}
function profit(buy,sell,quantity=1){return (Math.floor(sell*.95)-buy)*quantity;}
const API={W,STYLES,FORMATIONS,ROWS,POS,positions,meta,chemistry,squadRating,autoSquad,requirementRules,individualOK,validateSbc,solveScore,solvePuzzle,eligibility,evolve,profit};
root.EzzTools=API;if(typeof module!=='undefined')module.exports=API;
})(typeof globalThis!=='undefined'?globalThis:this);
