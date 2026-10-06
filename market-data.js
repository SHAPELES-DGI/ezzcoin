/* Shared exact-item prices. Source time is the feed publication time. */
(() => {
  'use strict';
  const root = new URL('./', document.currentScript.src);
  let cached = null;
  let pending = null;
  let loadedAt = 0;
  async function fetchData(name) {
    if (!/^[a-z-]+\.json$/.test(name)) throw new Error('Invalid data filename');
    // Workflow commits do not trigger Pages builds. Read those public snapshots
    // from main, retaining the deployed copy if GitHub's raw host is unavailable.
    const urls = ['https://raw.githubusercontent.com/SHAPELES-DGI/ezzcoin/main/data/' + name,
                  new URL('data/' + name, root).href];
    for (const url of urls) {
      try {
        const response = await fetch(url + '?t=' + Math.floor(Date.now() / 60000), { cache: 'no-store', signal: AbortSignal.timeout(15000) });
        if (response.ok) return await response.json();
      } catch (_) { /* Try the deployed snapshot. */ }
    }
    throw new Error('Market data unavailable');
  }
  function validate(data) {
    if (data?.game !== 'FC 27' || !Array.isArray(data.rows) || data.cols?.join(',') !== 'id,console,pc,consoleState,pcState') throw new Error('Invalid market data');
    if (!Number.isFinite(Date.parse(data.publishedAt?.console)) || !Number.isFinite(Date.parse(data.publishedAt?.pc))) throw new Error('Missing source time');
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
      return cached;
    })();
    try { return await pending; } finally { pending = null; }
  }
  window.EzzcoinsMarket = { load, lookup, validate, fetchData };
})();
