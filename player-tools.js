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
  const compare = document.createElement('a'); compare.href = new URL('compare.html', root);
  if (Number.isSafeInteger(item) && item > 0) compare.href += '?ids=' + item + '&add=1';
  compare.textContent = 'Compare player';
  controls.append(graph, compare, builder, evo); box.parentElement.after(controls);
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
  // Report a wrong price or card detail. Reports go to Ezzcoins' Firestore "reports" collection,
  // whose rules only allow creating a report: visitors can't read, change or delete any report.
  try { addReport(); } catch {}
  function addReport() {
    if (typeof status.addEventListener !== 'function' || !document.head) return;
    const endpoint = 'https://firestore.googleapis.com/v1/projects/ezzcoin-d5316/databases/(default)/documents/reports?key=AIzaSyDV6oQlHWc1mFCeo-ywnjy47nbq1lNvCD8';
    const sentKey = 'ezzReport:' + location.pathname;
    const css = document.createElement('style');
    css.textContent = '.ezz-report-open{display:inline-block;background:none;border:0;padding:10px 0;min-height:44px;color:#a9b8dc;font:13px system-ui,sans-serif;text-decoration:underline;text-underline-offset:3px;cursor:pointer}' +
      '.ezz-report-open:hover{color:#ffce66}.ezz-report{border:1px solid #40567d;border-radius:12px;background:#101a38;color:#eef3ff;padding:14px 16px;margin:4px 0 18px;max-width:560px;font:14px/1.45 system-ui,sans-serif}' +
      '.ezz-report fieldset{border:0;margin:0 0 12px;padding:0;display:grid;gap:4px}.ezz-report legend{font-weight:600;margin-bottom:6px;padding:0}' +
      '.ezz-report label{display:flex;gap:10px;align-items:center;min-height:36px;cursor:pointer}.ezz-report input[type=radio]{width:18px;height:18px;margin:0;accent-color:#ffce66}' +
      '.ezz-report .note{display:grid;gap:6px;min-height:0}.ezz-report textarea{box-sizing:border-box;width:100%;border:1px solid #52658c;border-radius:8px;background:#0b1430;color:#eef3ff;padding:9px 10px;font:14px/1.4 system-ui,sans-serif;resize:vertical}' +
      '.ezz-report .actions{display:flex;gap:8px;margin-top:12px;flex-wrap:wrap}.ezz-report .actions button{min-height:44px;padding:10px 16px;border-radius:9px;border:1px solid #52658c;background:#192b4d;color:#ffce66;font:600 13px system-ui,sans-serif;cursor:pointer}' +
      '.ezz-report .actions button[data-cancel]{background:transparent;color:#c9d3ec}.ezz-report .actions button:disabled{opacity:.6;cursor:wait}.ezz-report .msg{margin:10px 0 0;color:#9bedd2}.ezz-report .msg.bad{color:#ffb4a6}';
    document.head.append(css);
    const open = document.createElement('button'); open.type = 'button'; open.className = 'ezz-report-open';
    open.textContent = 'Spotted a wrong price or card detail? Report it';
    open.setAttribute('aria-expanded', 'false');
    const form = document.createElement('form'); form.className = 'ezz-report'; form.hidden = true; form.noValidate = true;
    form.innerHTML = '<fieldset><legend>What looks wrong?</legend>' +
      '<label><input type="radio" name="kind" value="price" checked> The price</label>' +
      '<label><input type="radio" name="kind" value="details"> Card details (rating, stats, club, position)</label>' +
      '<label><input type="radio" name="kind" value="other"> Something else</label></fieldset>' +
      '<label class="note">Tell us more (optional)<textarea name="note" rows="3" maxlength="500" placeholder="For example: it costs 12,500 in game right now"></textarea></label>' +
      '<div class="actions"><button type="submit">Send report</button><button type="button" data-cancel>Cancel</button></div>' +
      '<p class="msg" aria-live="polite"></p>';
    status.after(open, form);
    const msg = form.querySelector('.msg'), send = form.querySelector('button[type=submit]');
    const say = (text, bad) => { msg.textContent = text; msg.className = 'msg' + (bad ? ' bad' : ''); };
    const show = on => { form.hidden = !on; open.setAttribute('aria-expanded', String(on)); if (on) { say(''); form.querySelector('input[name=kind]:checked').focus(); } };
    open.addEventListener('click', () => show(form.hidden));
    form.querySelector('[data-cancel]').addEventListener('click', () => { show(false); open.focus(); });
    form.addEventListener('submit', async event => {
      event.preventDefault();
      let last = 0; try { last = Number(localStorage.getItem(sentKey)) || 0; } catch {}
      if (Date.now() - last < 10 * 60000) { say('Thanks, your report for this card is already in.'); return; }
      const data = new FormData(form);
      const fields = {
        kind: { stringValue: ['price', 'details', 'other'].includes(data.get('kind')) ? data.get('kind') : 'other' },
        note: { stringValue: String(data.get('note') || '').trim().slice(0, 500) },
        page: { stringValue: location.pathname.slice(0, 200) },
      };
      if (Number.isSafeInteger(item) && item > 0) fields.item = { integerValue: String(item) };
      if (latest && Number.isFinite(Number(latest.price))) {
        fields.price = { integerValue: String(Math.round(Number(latest.price))) };
        if (latest.at) fields.priceAt = { stringValue: String(latest.at).slice(0, 40) };
      }
      send.disabled = true; say('Sending…');
      try {
        const r = await fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ fields }), signal: AbortSignal.timeout(15000) });
        if (!r.ok) throw new Error('HTTP ' + r.status);
        try { localStorage.setItem(sentKey, String(Date.now())); } catch {}
        form.reset(); say('Thanks! Your report was sent. We check every report.');
      } catch { say('Couldn’t send it right now. Try again in a minute.', true); }
      finally { send.disabled = false; }
    });
  }
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
