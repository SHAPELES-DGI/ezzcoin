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
    // The site's own copy first. The server pulls every update within a minute, and it revalidates by ETag, so an
    // unchanged file costs a few bytes instead of a full download. GitHub's copy is only fetched when the own copy
    // is missing, broken or more than 30 minutes old (then the newer of the two wins).
    // Price history lives on its own "history" branch (replaced on every update, so it doesn't grow the
    // repository); the site's own data/ copy only exists on the GitHub Pages backup.
    const github = name.startsWith('price-history/')
      ? 'https://raw.githubusercontent.com/SHAPELES-DGI/ezzcoin/history/' + name
      : 'https://raw.githubusercontent.com/SHAPELES-DGI/ezzcoin/main/data/' + name;
    const time = data => name==='live-prices.json'?Math.min(Date.parse(data.publishedAt?.console)||0,Date.parse(data.publishedAt?.pc)||0):Date.parse(data.retrievedAt || data.updatedAt || data.at || '') || 0;
    const get = async (url, own) => {
      // GitHub: bypass its CDN cache.
      const response = await fetch(own ? url : url + '?t=' + Math.floor(Date.now() / 60000), { cache: own ? 'no-cache' : 'no-store', signal: AbortSignal.timeout(15000) });
      if (!response.ok) throw new Error('Snapshot unavailable');
      const data = await response.json();
      if (name === 'live-prices.json') validate(data);
      return data;
    };
    const available = [];
    try {
      const mine = await get(new URL('data/' + name, root).href, true);
      const at = time(mine);
      if (!at || Date.now() - at < 30 * 60000) return mine;
      available.push(mine);
    } catch (_) { /* Use GitHub's copy. */ }
    try { available.push(await get(github, false)); } catch (_) { /* Keep the own copy, if any. */ }
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
    // Several parts of a page refresh every minute; a forced reload within 50 seconds of the last one shares it.
    if (cached && Date.now() - loadedAt < (force ? 50000 : 300000)) return cached;
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
