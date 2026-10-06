const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const feed = at => ({game:'FC 27', cols:['id','console','pc','consoleState','pcState'], rows:[[123,1500,1700,0,0]], retrievedAt:at, publishedAt:{console:at,pc:at}, source:'FUT.GG'});
const old = feed('2026-10-06T18:00:00Z'), fresh = feed('2026-10-06T19:00:00Z');
let events = [];
const context = {URL, Date, Map, AbortSignal, CustomEvent:class {constructor(type, options){this.type=type;this.detail=options.detail;}},document:{currentScript:{src:'https://ezzcoins.com/market-data.js'}},window:{dispatchEvent:e=>events.push(e)}, fetch:async url=>({ok:true,json:async()=>url.includes('raw.githubusercontent')?old:fresh})};
vm.createContext(context);vm.runInContext(fs.readFileSync('market-data.js','utf8'),context);
(async()=>{
  const data=await context.window.EzzcoinsMarket.load(true);
  assert.equal(data.retrievedAt,fresh.retrievedAt);
  assert.equal(context.window.EzzcoinsMarket.lookup(data,123).price,1500);
  assert.equal(events[0].type,'ezzcoins:quotes');
  assert.equal(events[0].detail,data);
  context.fetch=async url=>{if(url.includes('raw.githubusercontent'))return {ok:true,json:async()=>fresh};throw Error('deployed unavailable');};
  assert.equal((await context.window.EzzcoinsMarket.fetchData('live-prices.json')).retrievedAt,fresh.retrievedAt);
  console.log('Newest snapshot selection, shared quote event and source fallback pass');
})().catch(error=>{console.error(error);process.exitCode=1;});
