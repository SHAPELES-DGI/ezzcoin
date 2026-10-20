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
  const moved=context.window.EzzcoinsMarket.validate({...fresh, rows:[[123,1500,1700,0,0],[247090+50331648,4900,5200,0,0],[555,800,900,0,0],[555+50331648,9000,9900,0,0]]});
  assert.equal(context.window.EzzcoinsMarket.lookup(moved,247090).price,4900,'a transferred player falls back to his new base item');
  assert.equal(context.window.EzzcoinsMarket.lookup(moved,555).price,800,'an existing base row always wins');
  assert.equal(context.window.EzzcoinsMarket.lookup(moved,999),null);
  assert.equal(events[0].type,'ezzcoins:quotes');
  assert.equal(events[0].detail,data);
  context.fetch=async url=>{if(url.includes('raw.githubusercontent'))return {ok:true,json:async()=>fresh};throw Error('deployed unavailable');};
  assert.equal((await context.window.EzzcoinsMarket.fetchData('live-prices.json')).retrievedAt,fresh.retrievedAt);
  const own='https://ezzcoins.com/live/', lane='https://raw.githubusercontent.com/SHAPELES-DGI/ezzcoin/live/';
  const live={...feed(new Date().toISOString()), lane:'live'}, mine={...feed(new Date().toISOString()), lane:'own'};
  const stale=d=>({...d,publishedAt:{console:'2026-10-06T00:00:00Z',pc:'2026-10-06T00:00:00Z'}});
  let asked=[], modes=[];
  // 1. The server's own copy is fresh: used alone, revalidated by ETag (no cache-busting query).
  context.fetch=async(url,opt)=>{asked.push(url);modes.push(opt&&opt.cache);return {ok:true,json:async()=>url.startsWith(own)?mine:url.startsWith(lane)?live:fresh};};
  assert.equal((await context.window.EzzcoinsMarket.fetchData('live-prices.json')).lane,'own');
  assert.deepEqual(asked,[own+'live-prices.json']);
  assert.deepEqual(modes,['no-cache']);
  // 2. No copy on the server (or the GitHub Pages backup): GitHub's live branch, cache-busted.
  asked=[];modes=[];
  context.fetch=async(url,opt)=>{asked.push(url);modes.push(opt&&opt.cache);if(url.startsWith(own))return {ok:false,json:async()=>({})};return {ok:true,json:async()=>url.startsWith(lane)?live:fresh};};
  assert.equal((await context.window.EzzcoinsMarket.fetchData('live-prices.json')).lane,'live');
  assert.equal(asked.length,2);
  assert(asked[1].startsWith(lane+'live-prices.json?t=')&&modes[1]==='no-store');
  // 3. The server's copy has gone stale (its sync stopped): GitHub's fresh copy wins.
  context.fetch=async url=>({ok:true,json:async()=>url.startsWith(own)?stale(mine):url.startsWith(lane)?live:fresh});
  assert.equal((await context.window.EzzcoinsMarket.fetchData('live-prices.json')).lane,'live');
  // 4. Both live copies stale or missing: the main-branch copies, as before.
  context.fetch=async url=>({ok:true,json:async()=>url.startsWith(own)?stale(mine):url.startsWith(lane)?stale(live):fresh});
  assert.equal((await context.window.EzzcoinsMarket.fetchData('live-prices.json')).retrievedAt,fresh.retrievedAt);
  context.fetch=async url=>{if(url.startsWith(lane)||url.startsWith(own))return {ok:false,json:async()=>({})};return {ok:true,json:async()=>fresh};};
  assert.equal((await context.window.EzzcoinsMarket.fetchData('live-prices.json')).retrievedAt,fresh.retrievedAt);
  asked=[];context.fetch=async url=>{asked.push(url);return {ok:true,json:async()=>fresh};};
  await context.window.EzzcoinsMarket.fetchData('players.json');
  assert(!asked.some(url=>url.startsWith(lane)||url.startsWith(own)));
  console.log('Newest snapshot selection, shared quote event and source fallback pass');
  console.log('Live lane: own-server copy first, then GitHub; stale or missing live copies fall back to main-branch copies');
})().catch(error=>{console.error(error);process.exitCode=1;});
