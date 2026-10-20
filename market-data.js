/* Shared exact-item prices. Source time is the feed publication time. */
(() => {
  'use strict';
  const root = new URL('./', document.currentScript.src);
  let cached = null;
  let pending = null;
  let loadedAt = 0;
  // Fast lane: the live branch is republished within minutes of each FUT.GG price release. Ezzcoins' server
  // copies it into live/ every 30 seconds, so visitors load it from ezzcoins.com; GitHub's copy is the fallback
  // (also for the GitHub Pages backup of the site, which has no live/ folder).
  // A copy is used only while it is fresh; otherwise the main-branch copies below are compared as before.
  const LIVE_BASES = [new URL('live/', root).href, 'https://raw.githubusercontent.com/SHAPELES-DGI/ezzcoin/live/'];
  const LIVE_FILES = new Set(['live-prices.json']);
  async function fetchLive(name) {
    for (const base of LIVE_BASES) {
      try {
        // Own server: revalidate by ETag, so an unchanged 440 KB file costs a few bytes. GitHub: bypass its CDN cache.
        const own = base.startsWith(root.href);
        const response = await fetch(base + name + (own ? '' : '?t=' + Math.floor(Date.now() / 60000)), { cache: own ? 'no-cache' : 'no-store', signal: AbortSignal.timeout(10000) });
        if (!response.ok) throw new Error('Live copy unavailable');
        const data = await response.json();
        const published = Date.parse(data?.publishedAt?.console || '') || 0;
        validate(data);
        if (Date.now() - published > 30 * 60000 || Date.now() - Date.parse(data.publishedAt.pc) > 30 * 60000) throw new Error('Live copy is stale');
        return data;
      } catch (_) { /* Try the next copy. */ }
    }
    throw new Error('Live copy unavailable');
  }
  async function fetchData(name) {
    if (!/^(?:[a-z-]+|price-history\/[0-9]{2})\.json$/.test(name)) throw new Error('Invalid data filename');
    if (LIVE_FILES.has(name)) {
      try { return await fetchLive(name); } catch (_) { /* Fall back to the main-branch copies. */ }
    }
    // Compare deployment and repository copies: either CDN can lag a refresh.
    // Use the newest timestamp and retain either host as an availability fallback.
    const urls = [new URL('data/' + name, root).href,
                  'https://raw.githubusercontent.com/SHAPELES-DGI/ezzcoin/main/data/' + name];
    const candidates = await Promise.allSettled(urls.map(async url => {
      try {
        const response = await fetch(url + '?t=' + Math.floor(Date.now() / 60000), { cache: 'no-store', signal: AbortSignal.timeout(15000) });
        if (response.ok) return await response.json();
      } catch (_) { /* Try the deployed snapshot. */ }
      throw new Error('Snapshot unavailable');
    }));
    const available = candidates.filter(r => r.status === 'fulfilled').map(r => r.value);
    const time = data => name==='live-prices.json'?Math.min(Date.parse(data.publishedAt?.console)||0,Date.parse(data.publishedAt?.pc)||0):Date.parse(data.retrievedAt || data.updatedAt || data.at || '') || 0;
    available.sort((a, b) => time(b) - time(a));
    if (name === 'live-prices.json') {
      for (const value of available) { try { validate(value); return value; } catch (_) {} }
      throw new Error('No valid price snapshot');
    }
    if (available.length) return available[0];
    throw new Error('Market data unavailable');
  }
  function validate(data) {
    if (data?.game !== 'FC 27' || !Array.isArray(data.rows) || data.cols?.join(',') !== 'id,console,pc,consoleState,pcState') throw new Error('Invalid market data');
    if (!Number.isFinite(Date.parse(data.publishedAt?.console)) || !Number.isFinite(Date.parse(data.publishedAt?.pc))) throw new Error('Missing source time');
    if (data.rows.some(r => !Array.isArray(r) || r.length !== 5 || !Number.isSafeInteger(r[0]) || r[0] <= 0 || [1,2].some(c => r[c] !== null && (!Number.isInteger(r[c]) || r[c] <= 0 || r[c] > 15000000)) || [3,4].some(c => !Number.isInteger(r[c]) || r[c] < 0 || r[c] > 4)) || new Set(data.rows.map(r=>r[0])).size !== data.rows.length) throw new Error('Invalid price rows');
    return { ...data, byId: new Map(data.rows.map(row => [row[0], row])) };
  }
  // A player who changes club gets a new base item from EA (old id + 3 × 2^24) and the feed lists only that one.
  const TRANSFER_OFFSET = 50331648;
  function lookup(data, id, platform = 'console') {
    const n = Number(id);
    const row = data?.byId.get(n) || (n > 0 && n < 16777216 ? data?.byId.get(n + TRANSFER_OFFSET) : undefined);
    if (!row) return null;
    const col = platform === 'pc' ? 2 : 1;
    const status = row[col + 2];
    const quote = data.quoteMetadata?.[String(row[0])]?.[platform];
    return { id: row[0], price: status === 0 && row[col] > 0 ? row[col] : null, status,
      at: quote?.at || data.publishedAt[platform], src: quote?.src || data.source, hist: [], ...freshness(quote?.at || data.publishedAt[platform]) };
  }
  async function load(force = false) {
    if (pending) return pending;
    if (!force && cached && Date.now() - loadedAt < 300000) return cached;
    pending = (async () => {
      const next = validate(await fetchData('live-prices.json'));
      cached = next;
      loadedAt = Date.now();
      window.dispatchEvent(new CustomEvent('ezzcoins:quotes', { detail: cached }));
      return cached;
    })();
    try { return await pending; } catch (error) {
      window.dispatchEvent(new CustomEvent('ezzcoins:quote-error', {detail:{message:error.message,lastSuccess:loadedAt}}));
      if (cached) return cached;
      throw error;
    } finally { pending = null; }
  }
  function freshness(at, now = Date.now()) {
    const timestamp = Date.parse(at), age = Math.max(0, now - timestamp);
    const state = !Number.isFinite(timestamp) || timestamp > now + 300000 || age > 90*60000 ? 'stale' : age > 15*60000 ? 'delayed' : 'fresh';
    return {freshness:state,ageMinutes:Number.isFinite(age)?Math.floor(age/60000):null,usable:state==='fresh'};
  }
  async function history(id, platform='console', days=7) {
    const data = await fetchData('price-history/'+String(Number(id)%64).padStart(2,'0')+'.json');
    return (data.items?.[String(id)]?.[platform] || []).filter(p=>p[0]*1000>=Date.now()-days*86400000);
  }
  window.EzzcoinsMarket = { load, lookup, validate, fetchData, freshness, history, get lastSuccess(){return loadedAt;} };
  if (typeof window.setInterval === 'function') window.setInterval(()=>{if(!document.hidden)load(true).catch(()=>{});},60000);
  document.addEventListener?.('visibilitychange',()=>{if(!document.hidden)load(true).catch(()=>{});});
})();
