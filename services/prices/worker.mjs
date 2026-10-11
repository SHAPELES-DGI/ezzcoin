const KEY = 'live-prices.json';
const COLS = ['id', 'console', 'pc', 'consoleState', 'pcState'];
const ORIGIN = 'https://r2.fut.gg/27/';

async function getJSON(url, fetcher) {
  const response = await fetcher(url, {redirect: 'error', signal: AbortSignal.timeout(15000),
    headers: {'Accept': 'application/json', 'User-Agent': 'Ezzcoins/1.0 price service'}});
  if (!response.ok) throw new Error(`Price source returned HTTP ${response.status}`);
  return response.json();
}

export function decode(manifest, index, consolePrices, pcPrices, now = Date.now()) {
  if (![index, consolePrices, pcPrices].every(x => x?.v === 2)) throw new Error('Unsupported price format');
  if (!Number.isSafeInteger(index.id0) || !Array.isArray(index.d)) throw new Error('Invalid item index');
  const ids = [index.id0];
  for (const delta of index.d) {
    if (!Number.isSafeInteger(delta) || delta <= 0) throw new Error('Invalid item delta');
    ids.push(ids.at(-1) + delta);
  }
  if (ids.length < 15000 || ids.some(id => !Number.isSafeInteger(id) || id <= 0)) throw new Error('Incomplete item index');
  for (const prices of [consolePrices, pcPrices]) {
    if (!Array.isArray(prices.p) || !Array.isArray(prices.s) || prices.p.length !== ids.length || prices.s.length !== ids.length)
      throw new Error('Price/index length mismatch');
    if (prices.p.some(p => !Number.isInteger(p) || p < 0 || p > 15000000) ||
        prices.s.some(s => !Number.isInteger(s) || s < 0 || s > 4)) throw new Error('Invalid price or card status');
  }
  const publishedAt = {};
  for (const [platform, name] of [['console', 'player-prices-ps5-dyn'], ['pc', 'player-prices-pc-dyn']]) {
    const stamp = manifest._published_at?.[name];
    if (!Number.isFinite(stamp) || stamp * 1000 > now + 300000 || stamp * 1000 < now - 1800000)
      throw new Error('Source publication time is invalid or more than 30 minutes old');
    publishedAt[platform] = new Date(stamp * 1000).toISOString();
  }
  const rows = ids.map((id, i) => [id,
    consolePrices.s[i] === 0 && consolePrices.p[i] > 0 ? consolePrices.p[i] : null,
    pcPrices.s[i] === 0 && pcPrices.p[i] > 0 ? pcPrices.p[i] : null,
    consolePrices.s[i], pcPrices.s[i]]);
  return {game: 'FC 27', source: 'FUT.GG', sourceUrl: 'https://www.fut.gg/',
    retrievedAt: new Date(now).toISOString(), publishedAt, priceType: 'lowestBuyNow', cols: COLS, rows,
    coverage: {feedCards: rows.length, consolePriced: rows.filter(r => r[1] !== null).length,
      pcPriced: rows.filter(r => r[2] !== null).length},
    statusLabels: {'0': 'Market card', '1': 'SBC', '2': 'Objective', '3': 'No market price', '4': 'Token reward'}};
}

export async function refresh(env, fetcher = fetch, now = Date.now()) {
  try {
    const manifest = await getJSON(ORIGIN + 'manifest.json', fetcher);
    const names = ['player-prices-index', 'player-prices-ps5-dyn', 'player-prices-pc-dyn'];
    if (![manifest._version, ...names.map(n => manifest[n])].every(v => /^[a-zA-Z0-9_-]+$/.test(String(v ?? ''))))
      throw new Error('Invalid source manifest');
    const blobs = await Promise.all(names.map(n => getJSON(`${ORIGIN}${n}.v${manifest._version}.${manifest[n]}.json`, fetcher)));
    const snapshot = decode(manifest, ...blobs, now);
    const oldObject = await env.PRICE_SNAPSHOTS.get(KEY);
    if (oldObject) {
      const old = await oldObject.json();
      if (['console', 'pc'].some(p => Date.parse(old.publishedAt?.[p]) > Date.parse(snapshot.publishedAt[p])))
        throw new Error('Source would move prices backwards');
    }
    await env.PRICE_SNAPSHOTS.put(KEY, JSON.stringify(snapshot), {
      httpMetadata: {contentType: 'application/json'},
      customMetadata: {retrievedAt: snapshot.retrievedAt, consoleAt: snapshot.publishedAt.console, pcAt: snapshot.publishedAt.pc}});
    await env.PRICE_SNAPSHOTS.put('status.json', JSON.stringify({ok: true, checkedAt: snapshot.retrievedAt}));
    return snapshot;
  } catch (error) {
    await env.PRICE_SNAPSHOTS.put('status.json', JSON.stringify({ok: false,
      checkedAt: new Date(now).toISOString(), error: String(error.message).slice(0, 180)}));
    throw error; // Keep the last good snapshot and surface failed cron runs in logs.
  }
}

export default {
  async scheduled(event, env, ctx) { ctx.waitUntil(refresh(env)); },
  async fetch(request, env) {
    const path = new URL(request.url).pathname;
    const headers = {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
      'Content-Type': 'application/json', 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'};
    if (request.method === 'OPTIONS') return new Response(null, {status: 204, headers});
    if (!['GET', 'HEAD'].includes(request.method)) return new Response('{"error":"Method not allowed"}', {status: 405, headers});
    if (!['/live-prices.json', '/health'].includes(path)) return new Response('{"error":"Not found"}', {status: 404, headers});
    const object = await env.PRICE_SNAPSHOTS.get(KEY);
    if (path === '/health') {
      const last = await env.PRICE_SNAPSHOTS.get('status.json');
      const status = last ? await last.json() : null;
      const stamps = object?.customMetadata || {};
      const fresh = ['consoleAt', 'pcAt'].every(k => Date.now() - Date.parse(stamps[k]) < 1800000);
      return Response.json({ok: Boolean(object && fresh && status?.ok), snapshot: stamps, lastRefresh: status},
        {status: object && fresh && status?.ok ? 200 : 503, headers});
    }
    if (!object) return new Response('{"error":"Price service has not completed its first refresh"}', {status: 503, headers});
    headers['X-Price-Source'] = 'FUT.GG';
    headers['X-Price-Retrieved-At'] = object.customMetadata?.retrievedAt || '';
    return new Response(request.method === 'HEAD' ? null : object.body, {headers});
  }
};
