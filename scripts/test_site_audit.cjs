const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..'),S=require('../site-utils.js'),P=require('../prices-core.js'),C=require('../tools-core.js');
const read=name=>JSON.parse(fs.readFileSync(path.join(root,name),'utf8'));
for(const [name,search] of [['ØDEGAARD','odegaard'],['João Félix','joao felix'],['Groß','gross'],['Łukasz','lukasz'],['Kjær','kjaer']])assert.equal(S.normalize(name),search);
const lookup=(data,id)=>{const row=data.byId.get(id)||data.byId.get(id+50331648);return row?{id:row[0]}:null;};
const roster={cols:['id','name','ovr','pos','club','nation'],rows:[[42,'Transferred player',80,'CM','Old club','Spain']]};
const extras={cols:['id','baseId','name','ovr','pos','version','club','nation','url'],rows:[[50331690,42,'Transferred player',80,'CM','Rare','New club','Spain',''],[841001,42,'Transferred player',85,'CM','Team of the Week','New club','Spain','']]};
const feed={rows:[[50331690,100,200,0,0],[841001,1000,2000,0,0]]};feed.byId=new Map(feed.rows.map(r=>[r[0],r]));
const cards=P.buildCards(roster,extras,feed,lookup);
assert.equal(cards.length,2,'transferred base appears once; genuine special remains separate');
assert.equal(cards.find(c=>c.id===50331690).type,'base');assert.equal(cards.find(c=>c.id===50331690).club,'New club');
assert.equal(cards.find(c=>c.id===841001).type,'special');
if(process.argv?.includes('--catalogue')){
 const current=read('data/live-prices.json');current.byId=new Map(current.rows.map(r=>[r[0],r]));
 const all=P.buildCards(read('data/players.json'),read('data/market-cards.json'),current,lookup,[...read('data/newcards.json').cards,...read('data/legends.json').cards],read('data/card-ids.json'));
 assert.equal(new Set(all.map(c=>c.id)).size,all.length);
 const broken=all.filter(c=>c.url.startsWith('p/')&&!fs.existsSync(path.join(root,c.url,'index.html')));
 assert.equal(broken.length,0,'all internal price-browser detail links exist: '+JSON.stringify(broken.slice(0,3)));
 console.log('Catalogue: '+all.length+' distinct items; all internal detail links exist.');
}
const card=(id,pos='ST',extra={})=>({id,baseId:id,pos,stats:[80,80,80,80,80,80],price:100,usable:true,...extra});
for(const extra of [{price:null},{price:NaN},{usable:false},{pos:'GK'}])assert(C.autoSquad([],['ST'],1000,[card(1,'ST',extra)]).error);
assert(C.autoSquad([],['ST','ST'],1000,[card(1),card(2,'ST',{baseId:1})]).error);
assert(C.autoSquad([card(1)],['ST'],NaN).error);
assert.equal(C.autoSquad([card(1)],['ST'],100,[card(1)]).cost,100);
assert.equal(C.meta(card(1), 'ST','Hunter',0),C.meta(card(1)),'zero chemistry gives no boost');
assert.equal(C.meta(card(1,'GK'),'GK','Hunter'),C.meta(card(1,'GK')),'outfield style cannot boost goalkeeper');
assert.equal(C.meta(card(1,'ST',{ps:'Quick Step+'})),C.meta(card(1))+2,'special-card PlayStyle+ is counted');
assert.equal(C.meta(card(1),'ST','Basic'),84,'meta uses the rounded boosted face stats shown on player pages');
assert.equal(Object.keys(C.STYLES).length,25);assert.equal(C.GK_STYLES.length,6);
const valid=()=>({version:1,trades:[],alerts:[],club:{},squad:{formation:'4-3-3',ids:[],styles:[],manager:{}}});
assert(C.validateState(valid()),'older valid exports remain importable');
const badDate=valid();badDate.trades=[{key:'trade',id:42,buy:100,quantity:1,date:'2026-02-31',platform:'console'}];assert.throws(()=>C.validateState(badDate));
const locked=valid();locked.squad.locks=[true,false];assert.deepEqual(C.validateState(locked).squad.locks,[true,false]);
for(const club of [[],{'1" onfocus="bad':{favourite:true}},JSON.parse('{"__proto__":null}'),{'1':{favourite:'yes'}},{'0':{favourite:true}}]){
  const state=valid();state.club=club;if(Object.keys(club).length||Array.isArray(club))assert.throws(()=>C.validateState(state));
}
for(const change of [s=>s.squad.ids=[-1],s=>s.squad.styles=['invented'],s=>s.squad.locks=['true'],s=>s.alerts=[{key:'a',id:0,target:100,direction:'below',platform:'pc'}]]){const state=valid();change(state);assert.throws(()=>C.validateState(state));}
console.log(`Site audit: transfer deduplication, search spelling, locked-card budgets, meta styles and backup validation pass.`);
