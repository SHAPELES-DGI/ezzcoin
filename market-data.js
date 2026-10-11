/* Shared exact-item prices. Source time is the feed publication time. */
(() => {
  'use strict';
  const root = new URL('./', document.currentScript.src);
  let cached = null;
  let pending = null;
  let loadedAt = 0;
  let serviceConfig;
  async function serviceURL() {
    if (!serviceConfig) serviceConfig = (async () => {
      try {
        const response = await fetch(new URL('data/price-service.json', root).href, {cache: 'no-store', signal: AbortSignal.timeout(5000)});
        if (!response.ok) return null;
        const {endpoint} = await response.json();
        if (!endpoint) return null;
        const url = new URL(endpoint);
        return url.protocol === 'https:' && !url.username && !url.password && url.pathname === '/live-prices.json' ? url.href : null;
      } catch (_) { return null; }
    })();
    return serviceConfig;
  }
  function mergeFeeds(feeds) {
    const valid = feeds.filter(data => { try { validate(data); return true; } catch (_) { return false; } });
    if (!valid.length) throw new Error('Market data unavailable');
    if (valid.length === 1) return valid[0];
    valid.sort((a, b) => (Date.parse(a.retrievedAt) || 0) - (Date.parse(b.retrievedAt) || 0));
    const newest = valid[valid.length - 1], rows = new Map(), quoteMetadata = {};
    const publishedAt = {};
    for (const platform of ['console', 'pc']) publishedAt[platform] = valid.reduce((at, f) =>
      Date.parse(f.publishedAt[platform]) > Date.parse(at) ? f.publishedAt[platform] : at, valid[0].publishedAt[platform]);
    for (const feed of valid) for (const row of feed.rows) {
      const merged = rows.get(row[0]) || [row[0], null, null, 3, 3];
      for (const [platform, col] of [['console', 1], ['pc', 2]]) {
        const metadata = feed.quoteMetadata?.[String(row[0])]?.[platform];
        const at = metadata?.at || feed.publishedAt[platform];
        const previous = quoteMetadata[String(row[0])]?.[platform];
        if (!previous || Date.parse(at) > Date.parse(previous.at)) {
          merged[col] = row[col]; merged[col + 2] = row[col + 2];
          (quoteMetadata[String(row[0])] ||= {})[platform] = {at, src: metadata?.src || feed.source,
            url: metadata?.url || feed.sourceUrl || 'https://www.fut.gg/'};
        }
      }
      rows.set(row[0], merged);
    }
    const combined = [...rows.values()];
    return {...newest, publishedAt, quoteMetadata, rows: combined, coverage: {...newest.coverage,
      feedCards: combined.length, consolePriced: combined.filter(r => r[1] !== null).length,
      pcPriced: combined.filter(r => r[2] !== null).length}};
  }
  async function fetchData(name) {
    if (!/^[a-z-]+\.json$/.test(name)) throw new Error('Invalid data filename');
    // Compare deployment and repository copies: either CDN can lag a refresh.
    // Use the newest timestamp and retain either host as an availability fallback.
    const urls = [new URL('data/' + name, root).href,
                  'https://raw.githubusercontent.com/SHAPELES-DGI/ezzcoin/main/data/' + name];
    if (name === 'live-prices.json') {
      const endpoint = await serviceURL();
      if (endpoint) urls.push(endpoint);
    }
    const candidates = await Promise.allSettled(urls.map(async url => {
      try {
        const response = await fetch(url + '?t=' + Math.floor(Date.now() / 60000), { cache: 'no-store', signal: AbortSignal.timeout(15000) });
        if (response.ok) return await response.json();
      } catch (_) { /* Try the deployed snapshot. */ }
      throw new Error('Snapshot unavailable');
    }));
    const available = candidates.filter(r => r.status === 'fulfilled').map(r => r.value);
    if (name === 'live-prices.json') return mergeFeeds(available);
    const time = data => Date.parse(data.retrievedAt || data.updatedAt || data.at || '') || 0;
    available.sort((a, b) => time(b) - time(a));
    if (available.length) return available[0];
    throw new Error('Market data unavailable');
  }
  function validate(data) {
    if (data?.game !== 'FC 27' || !Array.isArray(data.rows) || data.cols?.join(',') !== 'id,console,pc,consoleState,pcState') throw new Error('Invalid market data');
    if (!Number.isFinite(Date.parse(data.publishedAt?.console)) || !Number.isFinite(Date.parse(data.publishedAt?.pc))) throw new Error('Missing source time');
    if (data.rows.some(row => !Array.isArray(row) || row.length !== 5 || !Number.isSafeInteger(row[0]) || row[0] <= 0 ||
      [1, 2].some(col => row[col] !== null && (!Number.isInteger(row[col]) || row[col] <= 0 || row[col] > 15000000)) ||
      [3, 4].some(col => !Number.isInteger(row[col]) || row[col] < 0 || row[col] > 4)) ||
      new Set(data.rows.map(row => row[0])).size !== data.rows.length) throw new Error('Invalid quote rows');
    return { ...data, byId: new Map(data.rows.map(row => [row[0], row])) };
  }
  function lookup(data, id, platform = 'console') {
    const row = data?.byId.get(Number(id));
    if (!row) return null;
    const col = platform === 'pc' ? 2 : 1;
    const status = row[col + 2];
    const quote = data.quoteMetadata?.[String(id)]?.[platform];
    return { id: row[0], price: status === 0 && row[col] > 0 ? row[col] : null, status,
      at: quote?.at || data.publishedAt[platform], src: quote?.src || data.source, hist: [] };
  }
  async function load(force = false) {
    if (pending) return pending;
    if (!force && cached && Date.now() - loadedAt < 300000) return cached;
    pending = (async () => {
      cached = validate(await fetchData('live-prices.json'));
      loadedAt = Date.now();
      window.dispatchEvent(new CustomEvent('ezzcoins:quotes', { detail: cached }));
      return cached;
    })();
    try { return await pending; } finally { pending = null; }
  }
  window.EzzcoinsMarket = { load, lookup, validate, fetchData, mergeFeeds };
  if (typeof window.setInterval === 'function') window.setInterval(async () => {
    if (!document.hidden && await serviceURL()) load(true).catch(() => {});
  }, 60000);
})();
