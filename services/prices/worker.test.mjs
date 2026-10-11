import test from 'node:test';
import assert from 'node:assert/strict';
import worker, {decode, refresh} from './worker.mjs';

const now = Date.now();
function fixture() {
  return {manifest: {_version: 2, 'player-prices-index': 'index', 'player-prices-ps5-dyn': 'console',
    'player-prices-pc-dyn': 'pc', _published_at: {'player-prices-ps5-dyn': now / 1000, 'player-prices-pc-dyn': now / 1000}},
    index: {v: 2, id0: 1, d: Array(14999).fill(1)},
    console: {v: 2, p: Array(15000).fill(1500), s: Array(15000).fill(0)},
    pc: {v: 2, p: Array(15000).fill(2000), s: Array(15000).fill(0)}};
}
function bucket() {
  const data = new Map();
  return {data, async get(key) {const o = data.get(key); return o && {body: o.body, customMetadata: o.meta,
    json: async () => JSON.parse(o.body)};}, async put(key, body, opts = {}) {data.set(key, {body, meta: opts.customMetadata});}};
}
function fetcher(f) {
  let count = 0;
  const fn = async url => {count++; return Response.json(url.endsWith('manifest.json') ? f.manifest :
    url.includes('index') ? f.index : url.includes('ps5') ? f.console : f.pc);};
  fn.count = () => count; return fn;
}
test('exact card IDs, separate platforms and untradeable status', () => {
  const f = fixture(); f.console.s[0] = 1; f.pc.s[1] = 2;
  const d = decode(f.manifest, f.index, f.console, f.pc, now);
  assert.deepEqual(d.rows[0], [1, null, 2000, 1, 0]);
  assert.deepEqual(d.rows[1], [2, 1500, null, 0, 2]);
  assert.equal(d.coverage.consolePriced, 14999);
});
test('reject invalid, incomplete, stale and future feeds', () => {
  for (const corrupt of [f => {f.pc.p.pop();}, f => {f.index.d[0] = -1;},
    f => {f.console.s[0] = 9;}, f => {f.pc.p[0] = -10;},
    f => {f.manifest._published_at['player-prices-pc-dyn'] = (now - 1800001) / 1000;},
    f => {f.manifest._published_at['player-prices-pc-dyn'] = (now + 300001) / 1000;}]) {
    const f = fixture(); corrupt(f); assert.throws(() => decode(f.manifest, f.index, f.console, f.pc, now));
  }
});
test('successful refresh persists one validated snapshot using four source requests', async () => {
  const b = bucket(), fn = fetcher(fixture());
  const d = await refresh({PRICE_SNAPSHOTS: b}, fn, now);
  assert.equal(fn.count(), 4); assert.equal((await b.get('live-prices.json')).customMetadata.consoleAt, d.publishedAt.console);
  assert.equal((await (await b.get('status.json')).json()).ok, true);
});
test('denied source is not retried and cannot overwrite last good prices', async () => {
  const b = bucket(); await b.put('live-prices.json', '{"previous":true}'); let count = 0;
  await assert.rejects(refresh({PRICE_SNAPSHOTS: b}, async () => {count++; return new Response('', {status: 403});}, now), /403/);
  assert.equal(count, 1); assert.equal(b.data.get('live-prices.json').body, '{"previous":true}');
  assert.equal((await (await b.get('status.json')).json()).ok, false);
});
test('source timestamps cannot regress and older source cannot replace good data', async () => {
  const b = bucket(); await b.put('live-prices.json', JSON.stringify({publishedAt: {console: new Date(now + 1000).toISOString(), pc: new Date(now).toISOString()}}));
  const previous = b.data.get('live-prices.json').body;
  await assert.rejects(refresh({PRICE_SNAPSHOTS: b}, fetcher(fixture()), now), /backwards/);
  assert.equal(b.data.get('live-prices.json').body, previous);
});
test('public endpoints have CORS, missing data is unavailable, and no public writes exist', async () => {
  const env = {PRICE_SNAPSHOTS: bucket()};
  assert.equal((await worker.fetch(new Request('https://prices.test/live-prices.json'), env)).status, 503);
  assert.equal((await worker.fetch(new Request('https://prices.test/health'), env)).status, 503);
  assert.equal((await worker.fetch(new Request('https://prices.test/refresh', {method: 'POST'}), env)).status, 405);
  await refresh(env, fetcher(fixture()), now);
  const r = await worker.fetch(new Request('https://prices.test/live-prices.json'), env);
  assert.equal(r.headers.get('Access-Control-Allow-Origin'), '*'); assert.equal(r.status, 200);
  assert.equal((await r.json()).rows.length, 15000);
  assert.equal((await worker.fetch(new Request('https://prices.test/health'), env)).status, 200);
});
