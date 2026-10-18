/* One exact-item price renderer for every player page, including cards without stats. */
(async () => {
  'use strict';
  const script = document.currentScript;
  const box = document.getElementById('px');
  const M = window.EzzcoinsMarket;
  if (!box || !M || box.dataset.profileReady) return;
  box.dataset.profileReady = 'true';
  const root = new URL('./', script.src);
  const embedded = box.dataset.item;
  const match = location.pathname.match(/-(\d+)(?:\/index\.html)?\/?$/);
  let item = Number(embedded), checkedAt = null, latest = null, failed = false;
  if (embedded == null && match) {
    const page = Number(match[1]), key = page >= 1e9 ? page - 1e9 : page;
    if (page < 1e9) item = key;
    else {
      try { const ids = await M.fetchData('card-ids.json'); item = Number(ids[key] || (key > 16777216 ? key : 0)); }
      catch { item = key > 16777216 ? key : 0; }
    }
  }
  const reward = box.dataset.reward === 'true';
  const controls = document.createElement('div'); controls.className = 'ezz-profile-tools';
  const graph = document.createElement('button'); graph.type = 'button'; graph.textContent = 'Price graph';
  graph.dataset.playerName = document.querySelector('h1')?.textContent || 'Player';
  const builder = document.createElement('a'); builder.href = new URL('tools.html#squad', root); builder.textContent = 'Squad Builder';
  const evo = document.createElement('a'); evo.href = new URL('tools.html#evolutions', root); evo.textContent = 'Evolution Builder';
  controls.append(graph, builder, evo); box.parentElement.after(controls);
  const status = document.createElement('p'); status.className = 'ezz-profile-freshness';
  status.setAttribute('aria-live', 'polite'); controls.after(status);
  const footer = document.getElementById('price-source');
  function text(value) { if (status.textContent !== value) status.textContent = value; if (footer) footer.textContent = value; }
  function unavailable(message) {
    box.replaceChildren(); const note = document.createElement('span'); note.className = 'none'; note.textContent = message; box.append(note);
    delete box.dataset.price; status.className = 'ezz-profile-freshness'; text('Console · ' + message);
  }
  function render() {
    if (!latest || latest.price == null) return;
    const f = M.freshness(latest.at), label = failed ? 'CHECK FAILED' : f.freshness === 'fresh' ? 'LIVE' : f.freshness === 'delayed' ? 'DELAYED' : 'OUTDATED';
    const amount = document.createElement('b'), coin = document.createElement('i'); coin.className = 'coin';
    amount.append(coin, document.createTextNode(Number(latest.price).toLocaleString('en-US')));
    const badge = document.createElement('span'); badge.className = 'price-updated'; badge.textContent = label;
    const valid = Number.isFinite(Date.parse(latest.at)), time = valid ? new Date(latest.at).toLocaleString() : 'Source time unavailable'; badge.title = time;
    box.replaceChildren(amount, badge); box.dataset.price = latest.price;
    status.className = 'ezz-profile-freshness ' + f.freshness;
    const checkAge = checkedAt == null ? null : Math.max(0, Math.floor((Date.now() - checkedAt) / 60000));
    text((failed ? 'Price check failed · Saved quote · ' : '') + 'Console · ' + (latest.src || 'Source unavailable') + ' · ' + time + ' · ' + (f.freshness === 'fresh' ? 'Current quote' : f.freshness === 'delayed' ? 'Delayed quote' : 'Outdated quote') +
      (f.ageMinutes == null ? '' : ' · ' + f.ageMinutes + ' min ago') + (checkAge == null ? '' : ' · Ezzcoins checked ' + (checkAge < 1 ? 'just now' : checkAge + ' min ago')));
  }
  function update(data) {
    latest = reward ? null : M.lookup(data, item);
    if (reward) { unavailable('Reward card · not tradeable'); return; }
    if (!latest) { unavailable('No verified console quote for this card.'); return; }
    graph.dataset.priceGraph = latest.id;
    if (latest.price == null) {
      unavailable(({0:'No listings right now.',1:'SBC card · not tradeable',2:'Objective card · not tradeable',3:'Not on the transfer market',4:'Reward card · not tradeable'})[latest.status] || 'Price unavailable');
      return;
    }
    render();
  }
  if (Number.isSafeInteger(item) && item > 0 && !reward) graph.dataset.priceGraph = item;
  else { graph.disabled = true; graph.title = reward ? 'Reward cards cannot be traded.' : 'This card’s market identity is not verified.'; }
  window.addEventListener('ezzcoins:quotes', e => { failed = false; update(e.detail); });
  window.addEventListener('ezzcoins:quote-error', () => {
    failed = true;
    const badge = box.querySelector('.price-updated'); if (badge) badge.textContent = 'CHECK FAILED';
    text('Price check failed. The displayed saved quote may be outdated.');
  });
  setInterval(render, 60000);
  try { update(await M.load()); }
  catch { failed = true; const badge = box.querySelector('.price-updated'); if (badge) badge.textContent = 'CHECK FAILED'; text('Price check failed. The displayed saved quote may be outdated.'); }
  async function loadCheck() {
    try {
      const r = await fetch('https://raw.githubusercontent.com/SHAPELES-DGI/ezzcoin/check/check.json?t=' + Math.floor(Date.now()/60000), {cache:'no-store', signal:AbortSignal.timeout(10000)});
      if (!r.ok) return;
      const time = Date.parse((await r.json()).checkedAt);
      if (Number.isFinite(time) && time <= Date.now() + 300000) { checkedAt = time; render(); }
    } catch {}
  }
  loadCheck();
})();
