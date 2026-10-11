const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const stamp = n => `2026-10-11T14:${n}:00Z`;
const feed = (at, price, retrievedAt = at) => ({game: 'FC 27', source: 'FUT.GG',
  cols: ['id', 'console', 'pc', 'consoleState', 'pcState'], rows: [[123, price, price + 100, 0, 0]],
  retrievedAt, publishedAt: {console: at, pc: at}, coverage: {feedCards: 1}});
function setup(backend) {
  const context = {URL, Date, Map, Set, AbortSignal, CustomEvent: class {constructor(type, options) {this.type = type; this.detail = options.detail;}},
    document: {currentScript: {src: 'https://ezzcoins.com/market-data.js'}}, window: {dispatchEvent() {}},
    fetch: async url => {
      if (url.includes('price-service.json')) return {ok: true, json: async () => ({endpoint: 'https://price-service.test/live-prices.json'})};
      if (url.includes('price-service.test')) {if (backend instanceof Error) throw backend; return {ok: true, json: async () => backend};}
      return {ok: true, json: async () => feed(stamp('10'), 1500)};
    }};
  vm.createContext(context); vm.runInContext(fs.readFileSync('market-data.js', 'utf8'), context);
  return context.window.EzzcoinsMarket;
}
(async () => {
  let api = setup(feed(stamp('15'), 2500));
  assert.equal(api.lookup(await api.load(true), 123).price, 2500);
  api = setup(feed(stamp('05'), 9999, stamp('20')));
  assert.equal(api.lookup(await api.load(true), 123).price, 1500, 'later retrieval must not make old source newer');
  api = setup(new Error('service unavailable'));
  assert.equal(api.lookup(await api.load(true), 123).price, 1500);
  api = setup({...feed(stamp('20'), 9999), rows: [[123, -10, 10, 0, 0]]});
  assert.equal(api.lookup(await api.load(true), 123).price, 1500, 'invalid service must not discard good fallback');
  const local = feed(stamp('10'), 1500);
  local.quoteMetadata = {'123': {console: {src: 'FUTBIN', at: stamp('20')}}};
  const combined = api.mergeFeeds([local, feed(stamp('15'), 2500)]);
  assert.equal(api.lookup(api.validate(combined), 123).price, 1500);
  assert.equal(api.lookup(api.validate(combined), 123, 'pc').price, 2600);
  assert.equal(api.lookup(api.validate(combined), 123).src, 'FUTBIN');
  const reward = feed(stamp('25'), 0); reward.rows = [[123, null, null, 2, 2]];
  assert.equal(api.lookup(api.validate(api.mergeFeeds([local, reward])), 123).price, null);
  console.log('Service prices, source-time precedence, platform merging, invalid feed and outage fallbacks pass');
})().catch(error => {console.error(error); process.exitCode = 1;});
