/* Ezzcoins Dashboard Upgrade
   Additive layer: does not replace the site's existing updater, calculators or player DB.
*/
(() => {
  'use strict';

  const CONFIDENCE_INDEX = { low: 35, medium: 65, high: 85 };
  const STORAGE = {
    budget: 'ezzcoins_budget_v1',
    alerts: 'ezzcoins_alerts_v1'
  };

  const state = { snapshot: null, ledger: null, history: null, market: null, pulse: null };
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  const esc = s => String(s ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  const validPrice = n => n != null && n !== '' && Number.isFinite(+n) && +n > 0;
  const coins = n => n != null && n !== '' && Number.isFinite(+n) ? new Intl.NumberFormat("en-US").format(Math.round(+n)) : '—';
  const coinPrice = n => (validPrice(n) ? '<i class="coin" aria-hidden="true"></i>' : '') + coins(n);
  const clamp = (n,a,b) => Math.max(a,Math.min(b,n));
  const toneClass = tone => ['buy','sell','watch','hold'].includes(tone) ? tone : 'watch';
  const confidenceIndex = c => CONFIDENCE_INDEX[String(c || '').toLowerCase()] || 35;
  const getJSON = (key, fallback) => { try { return JSON.parse(localStorage.getItem(key) || '') || fallback; } catch { return fallback; } };
  const saveJSON = (key, value) => { try { localStorage.setItem(key, JSON.stringify(value)); } catch { toast('Browser storage is unavailable; this change will not persist.'); } };
  const savedAlerts = () => { const a = getJSON(STORAGE.alerts, []); return Array.isArray(a) ? a.filter(x => x && typeof x.key === 'string' && validPrice(x.target)) : []; };
  const isFresh = () => window.EzzcoinsMarket.freshness(state.market?.publishedAt?.console||state.snapshot?.updatedAt).usable;
  const ageNote = () => window.EzzcoinsMarket.freshness(state.market?.publishedAt?.console||state.snapshot?.updatedAt).freshness === 'delayed' ? 'Prices are more than 15 minutes old. Refresh before acting.' : 'Prices are unavailable or more than 90 minutes old. Refresh before acting.';

  function toast(message) {
    let el = $('.ez-toast');
    if (!el) { el = document.createElement('div'); el.className = 'ez-toast'; document.body.appendChild(el); }
    el.textContent = message; el.classList.add('show');
    clearTimeout(toast._t); toast._t = setTimeout(() => el.classList.remove('show'), 2400);
  }

  function humanTime(iso) {
    if (!iso) return 'Waiting for update';
    const d = new Date(iso); if (Number.isNaN(d.getTime())) return 'Waiting for update';
    const delta = Date.now() - d.getTime();
    const mins = Math.floor(delta / 60000);
    if (mins < 2) return 'Updated just now';
    if (mins < 60) return `Updated ${mins}m ago`;
    const hrs = Math.floor(mins/60);
    if (hrs < 24) return `Updated ${hrs}h ago`;
    return `Updated ${Math.floor(hrs/24)}d ago`;
  }

  function replaceTimeTokens(text) {
    return String(text || '').replace(/\{\{t:([^}]+)\}\}/g, (_, iso) => {
      const d = new Date(iso);
      return Number.isNaN(d.getTime()) ? iso : d.toLocaleString([], {weekday:'short',hour:'2-digit',minute:'2-digit'});
    });
  }

  function findInsertionPoint() {
    const now = $('#now');
    if (now) return { parent: now, before: now.firstElementChild };
    const main = $('main');
    if (main) return { parent: main, before: main.firstElementChild };
    const nav = $('nav');
    if (nav?.parentElement) return { parent: nav.parentElement, before: nav.nextElementSibling };
    const firstH2 = $('h2');
    if (firstH2?.parentElement) return { parent: firstH2.parentElement, before: firstH2 };
    return { parent: document.body, before: document.body.firstElementChild };
  }

  async function loadData() {
    const names = ['snapshot.json','ledger.json','history.json','market.json'];
    const results = await Promise.allSettled(names.map(name => window.EzzcoinsMarket.fetchData(name)));
    if (results[0].status === 'fulfilled') state.snapshot = results[0].value;
    if (results[1].status === 'fulfilled') state.ledger = results[1].value;
    if (results[2].status === 'fulfilled') state.history = results[2].value;
    if (results[3].status === 'fulfilled') state.pulse = results[3].value;
    try { state.market = await window.EzzcoinsMarket.load(true); } catch (_) {}
    for (const player of state.snapshot?.meta || []) {
      const quote = player.eaId && state.market ? window.EzzcoinsMarket.lookup(state.market, player.eaId) : null;
      player.price = quote?.price ?? null;
      player.priceAt = quote?.at;
      player.priceSrc = quote?.src;
    }
    try { await window.EzzcoinsCardArt.load(); } catch (_) {}
    return results.slice(0,3).some(r => r.status === 'fulfilled');
  }

  window.addEventListener('ezzcoins:quotes', event => {
    state.market = event.detail;
    for (const [index, player] of (state.snapshot?.meta || []).entries()) {
      const quote = player.eaId ? window.EzzcoinsMarket.lookup(state.market, player.eaId) : null;
      player.price = quote?.price ?? null; player.priceAt = quote?.at; player.priceSrc = quote?.src;
      const card = document.querySelector('[data-ez-player="'+index+'"]');
      if (card) {
        card.querySelector('.ez-player-price').innerHTML = coinPrice(player.price)+' <small>'+(validPrice(player.price)?'coins':'unavailable')+'</small>';
        card.querySelector('.ez-player-source').textContent = player.priceSrc || 'No quote';
        card.querySelector('.ez-player-meta').textContent = humanTime(player.priceAt);
      }
    }
    renderAlerts();
  });

  function gradedStats() {
    const calls = state.ledger?.calls || [];
    const graded = calls.filter(c => c.status === 'hit' || c.status === 'miss');
    const hits = graded.filter(c => c.status === 'hit');
    const resultVals = graded.filter(c => c.tone === 'buy' && c.result != null && c.result !== '').map(c => Number(c.result)).filter(Number.isFinite);
    // Lifetime totals: the call list is trimmed to the latest 60, the record keeps every graded call.
    const r = state.ledger?.record, n = r ? (+r.hit || 0) + (+r.miss || 0) : 0;
    if (r && n >= graded.length) return {
      graded: n, hits: +r.hit || 0, winRate: n ? (+r.hit || 0) / n * 100 : null,
      avg: +r.buyN > 0 ? (+r.buySum || 0) / +r.buyN : null, since: r.since
    };
    return {
      graded: graded.length,
      hits: hits.length,
      winRate: graded.length ? (hits.length / graded.length * 100) : null,
      avg: resultVals.length ? resultVals.reduce((a,b)=>a+b,0)/resultVals.length : null
    };
  }

  const STRATEGY_STATUS = {
    active: ['buy', 'Active', 'Used for new calls'],
    retest: ['watch', 'Retest', 'Back after a pause, at low confidence'],
    new: ['hold', 'Untested', 'No graded calls yet'],
    paused: ['sell', 'Paused', 'Recent calls lost after tax']
  };
  const pct = v => v == null || !Number.isFinite(+v) ? '–' : `${+v > 0 ? '+' : ''}${(+v).toFixed(1)}%`;
  const shortDate = iso => { const d = new Date(iso); return Number.isNaN(d.getTime()) ? '' : d.toLocaleDateString([], {day:'numeric', month:'short'}); };

  function strategiesHTML() {
    const board = Array.isArray(state.ledger?.strategyBoard) ? state.ledger.strategyBoard : [];
    if (!board.length) return '';
    return `<div class="ez-strats"><div class="ez-strats-head">How each strategy is doing</div>${board.map(b => {
      const [tone, label, hint] = STRATEGY_STATUS[b.status] || STRATEGY_STATUS.new;
      const n = (+b.hit || 0) + (+b.miss || 0);
      const line = n ? `${b.hit} of ${n} hit · ${pct(b.avg)} average after tax` + (+b.recentN && +b.recentN < n ? ` · last ${b.recentN}: ${pct(b.recentAvg)}` : '') : hint;
      const until = b.status === 'paused' && b.pausedUntil ? ` · back ${shortDate(b.pausedUntil)}` : '';
      return `<div class="ez-strat"><div class="ez-strat-top"><span class="ez-strat-name">${esc(b.name)}</span><span class="ez-pill ${tone}" title="${esc(hint)}">${esc(label)}</span></div>
        <div class="ez-strat-line">${esc(line + until)}</div></div>`;
    }).join('')}<div class="ez-disclaimer">A strategy is judged on its last 12 graded calls. Under 50% hits or a negative average after tax pauses it for 7 days.</div></div>`;
  }

  function bestFodder() {
    const f = (state.snapshot?.fodder || []).map(x => ({...x, cpp: validPrice(x.price) && x.score > 0 ? x.price/x.score : Infinity})).filter(x => Number.isFinite(x.cpp));
    if (!f.length) return null;
    f.sort((a,b)=>a.cpp-b.cpp);
    const best = f[0], near = f.filter(x => x.cpp - best.cpp < .1);
    return {best, near};
  }

  function heroHTML() {
    const s = state.snapshot, v = s?.verdict || {}, fresh = isFresh();
    const quotes = state.market?.coverage?.consolePriced;
    return `<section class="ez-hero">
      <div class="ez-hero-top"><div><div class="ez-kicker">THE EZZCOINS TRADING DESK</div>
        <h2>Your next move starts here.</h2>
        <p>Follow the market. Watch your players. Make a plan.</p></div>
        <a class="ez-market-link" href="prices.html">Explore the market <span aria-hidden="true">↗</span></a></div>
      <div class="ez-hero-stats">
        <div><span>Console quotes</span><strong>${quotes == null ? '—' : coins(quotes)}</strong><small>${esc(humanTime(state.market?.publishedAt?.console))}</small></div>
        <div><span>Price checks</span><strong>Every minute</strong><small>Source publication times vary</small></div>
        <div><span>Market commentary</span><strong>${esc(humanTime(s?.updatedAt))}</strong><small>${fresh ? 'Latest stored read' : 'Older read · review before acting'}</small></div>
      </div>
      <details class="ez-market-brief"><summary><span class="ez-pill hold">MARKET READ</span><span>${esc(v.label || 'Waiting for a market read')}</span><span class="ez-brief-toggle">+</span></summary>
        <p>${esc(replaceTimeTokens(v.detail || 'Market commentary is unavailable.'))}</p></details>
      <div class="ez-actions"><button class="ez-btn primary" data-ez-scroll="trades">Trade ideas <span aria-hidden="true">↓</span></button>
        <button class="ez-btn" data-ez-scroll="budget">Plan my coins</button>
        <button class="ez-btn ghost" data-ez-scroll="alerts">Price alerts</button>
        <button class="ez-btn ghost" data-ez-scroll="coach">Ask Coach</button></div>
      </section>`;
  }

  function tradesHTML() {
    const moves = state.snapshot?.moves || [];
    if (!moves.length) return '<p class="ez-card-sub">No trade calls right now. New ones arrive with the next market read.</p>';
    return `<div class="ez-trades">${moves.slice(0,4).map((m,i) => {
      const idx = confidenceIndex(m.confidence), tone = toneClass(m.tone);
      return `<article class="ez-trade" data-tone="${tone}">
        <div class="ez-trade-head"><span class="ez-pill ${tone}">${esc(m.tone || 'watch')}</span><span class="ez-trade-when">${esc(replaceTimeTokens(m.when || 'Current update'))}</span></div>
        <h4 class="ez-trade-title">${esc(m.title)}</h4>
        <p class="ez-trade-detail" id="ez-trade-detail-${i}">${esc(replaceTimeTokens(m.detail))}</p>
        <div class="ez-trade-foot">
          <button type="button" class="ez-trade-more" aria-expanded="false" aria-controls="ez-trade-detail-${i}">Show why</button>
          <span class="ez-confidence" title="Internal confidence index, not a win probability"><span class="ez-confbar"><i style="width:${idx}%"></i></span>${esc(String(m.confidence || 'low').replace(/^./, c => c.toUpperCase()))} confidence</span>
        </div>
      </article>`;
    }).join('')}</div>`;
  }
  function trackHTML() {
    const st = gradedStats();
    const wr = st.winRate == null ? '—' : `${Math.round(st.winRate)}%`;
    const avg = st.avg == null ? '—' : `${st.avg > 0 ? '+' : ''}${st.avg.toFixed(1)}%`;
    return `
      <div class="ez-metric ${st.winRate != null && st.winRate >= 60 ? 'ez-positive':''}">${wr}</div>
      <div class="ez-metric-label">graded-call win rate${st.since ? ` since ${esc(shortDate(st.since))}` : ''}</div>
      <div class="ez-mini-row"><span>Graded calls, all time</span><span>${st.graded}</span></div>
      <div class="ez-mini-row"><span>Hits</span><span>${st.hits}</span></div>
      <div class="ez-mini-row"><span>Avg BUY return after tax</span><span>${avg}</span></div>
      ${strategiesHTML()}
      <button class="ez-btn ghost" data-ez-record>Open full history</button>
      <div class="ez-disclaimer">Voided and open calls are excluded. Every call is graded automatically at its check time against the live price, after the 5% tax.</div>`;
  }

  // ---- 6 PM UK daily drop: times are worked out here, so the clock is right even if the read is old.
  const UK_PARTS = new Intl.DateTimeFormat('en-GB', {timeZone:'Europe/London', year:'numeric', month:'numeric', day:'numeric', hour:'numeric', minute:'numeric', second:'numeric', hourCycle:'h23'});
  function ukParts(ms) {
    const p = {}; for (const {type, value} of UK_PARTS.formatToParts(new Date(ms))) p[type] = +value;
    return p;
  }
  function ukWall(y, m, d, h) {   // the UTC time of a UK wall-clock time (day overflow is fine)
    const guess = Date.UTC(y, m - 1, d, h);
    const p = ukParts(guess);
    return guess - (Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute, p.second) - guess);
  }
  function dropClock(now = Date.now()) {
    const p = ukParts(now), today = ukWall(p.year, p.month, p.day, 18);
    const prev = today <= now ? today : ukWall(p.year, p.month, p.day - 1, 18);
    const next = today > now ? today : ukWall(p.year, p.month, p.day + 1, 18);
    const np = ukParts(next);
    return {prev, next, after: now - prev < 3 * 3600000, friday: new Date(Date.UTC(np.year, np.month - 1, np.day)).getUTCDay() === 5};
  }
  function span(ms) {
    const m = Math.max(0, Math.round(ms / 60000)), h = Math.floor(m / 60);
    return h ? `${h}h ${String(m % 60).padStart(2, '0')}m` : `${m}m`;
  }
  const localTime = ms => new Date(ms).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
  function clockHTML() {
    const c = dropClock(), now = Date.now();
    if (c.after) return `<span class="ez-drop-k">Today's drop landed</span><strong>${span(now - c.prev)} ago</strong>
      <small>Sell window runs to about ${esc(localTime(c.prev + 3 * 3600000))} your time · next drop in ${span(c.next - now)}</small>`;
    return `<span class="ez-drop-k">Next drop${c.friday ? ' · Friday promo night' : ''}</span><strong>${span(c.next - now)}</strong>
      <small>${esc(new Date(c.next).toLocaleString([], {weekday:'short', hour:'2-digit', minute:'2-digit'}))} your time · 6 PM UK</small>`;
  }
  function dropRow(label, a) {
    if (!a) return '';
    const measuring = (a.n || 0) < 5;
    const [tone, pill] = a.tone === 'buy' ? ['buy', 'Buy before'] : a.tone === 'hold' ? ['hold', 'Buy after'] : ['watch', measuring ? 'Measuring' : 'No edge'];
    return `<div class="ez-drop-row" data-tone="${tone}"><div class="ez-drop-row-top"><span class="ez-drop-what">${esc(label)}</span><span class="ez-pill ${tone}">${pill}</span></div>
      <p>${esc(replaceTimeTokens(a.text))}</p></div>`;
  }
  function dropHTML() {
    const d = state.snapshot?.dailyDrop;
    const cell = v => v == null || !Number.isFinite(+v) ? '<td class="ez-muted">–</td>' : `<td class="${+v > 1 ? 'ez-positive' : +v < -1 ? 'ez-danger' : ''}">${pct(v)}</td>`;
    const recent = Array.isArray(d?.recent) ? d.recent.slice(0, 5) : [];
    const table = recent.length ? `<div class="ez-drop-table-wrap"><table class="ez-drop-table"><caption>Last ${recent.length} drops: change from just before 6 PM to about 8 PM UK</caption>
      <thead><tr><th scope="col">Day</th><th scope="col">84s</th><th scope="col">85s</th><th scope="col">86s</th><th scope="col">Top 100</th></tr></thead>
      <tbody>${recent.map(r => `<tr><th scope="row">${esc(new Date(r.date + 'T12:00:00Z').toLocaleDateString([], {weekday:'short', day:'numeric'}))}${r.friday ? ' <span class="ez-drop-fri">Promo night</span>' : ''}</th>${cell(r.chg?.f84)}${cell(r.chg?.f85)}${cell(r.chg?.f86)}${cell(r.chg?.i100)}</tr>`).join('')}</tbody></table></div>` : '';
    const rows = d ? `<div class="ez-drop-group">${esc(d.group || '')} · ${esc(String(d.measured ?? 0))} drops measured so far</div>${dropRow('84 to 86 fodder', d.fodder)}${dropRow('Expensive meta cards', d.meta)}`
      : '<p class="ez-drop-group">The drop record appears with the next market read.</p>';
    return `<div class="ez-drop-top"><div class="ez-drop-clock" data-ez-drop-clock>${clockHTML()}</div><div class="ez-drop-rows">${rows}</div></div>${table}
      ${d ? `<div class="ez-disclaimer">${esc(d.method || '')} Past moves are no promise: a new SBC or promo can change any evening.</div>` : ''}`;
  }

  function fodderHTML() {
    const b = bestFodder();
    if (!b) return '<div class="ez-skeleton"></div>';
    const tie = b.near.length > 1;
    return `
      <div class="ez-metric">${tie ? b.near.map(x=>x.ovr).join('–') : b.best.ovr}</div>
      <div class="ez-metric-label">best Item Score value ${tie ? '(near-tie)' : ''}</div>
      <div class="ez-mini-row"><span>Lowest c / pt</span><span>${b.best.cpp.toFixed(2)}</span></div>
      <div class="ez-mini-row"><span>${b.best.ovr} floor</span><span>${coinPrice(b.best.price)}</span></div>
      <div class="ez-mini-row"><span>Score</span><span>${coins(b.best.score)}</span></div>`;
  }

  function allocationFor(budget) {
    if (!isFresh()) return [['Keep liquid', 100, ageNote()]];
    const moves = state.snapshot?.moves || [];
    const buys = moves.filter(m => m.tone === 'buy');
    const highRiskMarket = moves.some(m => /still falling|wait/i.test(m.title || '') || m.tone === 'hold');
    if (!buys.length) {
      return highRiskMarket ? [
        ['Keep liquid', 80, 'Wait for a confirmed buy setup'],
        ['SBC / squad use', 15, 'Only cards you actually need'],
        ['Test flips', 5, 'Small bids only; respect tax']
      ] : [
        ['Keep liquid', 60, 'Ready for the next market window'],
        ['Fodder value', 25, 'Only if the live board supports it'],
        ['Meta flips', 15, 'Small positions']
      ];
    }
    const conf = buys.map(b => confidenceIndex(b.confidence));
    const avgConf = conf.reduce((a,b)=>a+b,0)/conf.length;
    const buyPct = clamp(Math.round(avgConf * .65), 25, 60);
    return [
      ['Current BUY calls', buyPct, 'Split across the live buy calls'],
      ['Keep liquid', 100-buyPct-10, 'Reserve for new supply or dips'],
      ['Test flips', 10, 'Small positions only']
    ];
  }

  function budgetHTML() {
    const saved = Number(getJSON(STORAGE.budget, 50000));
    return `
      <div class="ez-budget-row">
        <input class="ez-input" id="ez-budget-input" type="number" min="0" step="1000" value="${Number.isFinite(saved)?saved:50000}" aria-label="Coin budget">
        <button class="ez-btn primary" id="ez-plan-btn">Build plan</button>
      </div>
      <div class="ez-chips" style="margin-top:10px">${[10000,25000,50000,100000,500000,1000000].map(n => `<button class="ez-chip" data-ez-budget="${n}">${n >= 1000000 ? '1m' : n/1000+'k'}</button>`).join('')}</div>
      <div id="ez-allocation" class="ez-allocation"></div>
      <div class="ez-disclaimer">This is an in-game coin allocation helper. It uses the current Ezzcoins calls and does not guarantee profit.</div>`;
  }

  function renderAllocation() {
    const input = $('#ez-budget-input'); if (!input) return;
    const budget = Math.max(0, Number(input.value || 0));
    if (!Number.isFinite(budget)) return toast('Enter a valid coin budget');
    saveJSON(STORAGE.budget, budget);
    const plan = allocationFor(budget);
    // Each part of the plan: name and amount on one line, the bar under them, then the note. Nothing overlaps on phones.
    $('#ez-allocation').innerHTML = plan.map(([label,pct,note]) => `
      <div class="ez-alloc"><div class="ez-alloc-top"><span class="ez-alloc-label">${esc(label)}</span><strong>${coinPrice(budget*pct/100)} <small>${pct}%</small></strong></div>
        <span class="ez-alloc-bar" role="img" aria-label="${pct}% of your coins"><i style="width:${pct}%"></i></span><div class="ez-alloc-note">${esc(note)}</div></div>`).join('');
  }

  function coachHTML() {
    const prompts = ['What should I buy right now?','I have 100k coins — what should I do?','Should I sell my fodder?','Best trade under 20k','What market event is next?'];
    return `<div class="ez-chips">${prompts.map(p => `<button class="ez-chip" data-ez-prompt="${esc(p)}">${esc(p)}</button>`).join('')}</div><div class="ez-coach-status" id="ez-coach-status" role="status">Quick answers from the stored Ezzcoins market calls.</div>`;
  }

  function alertsHTML() {
    const f = state.snapshot?.fodder || [];
    const opts = f.map(x => `<option value="fodder:${x.ovr}" data-price="${x.price}">${x.ovr}-rated fodder · ${coins(x.price)}</option>`).join('');
    const players = (state.snapshot?.meta || []).map(x => `<option value="player:${esc(x.name)}" data-price="${x.price}">${esc(x.name)} · ${coins(x.price)}</option>`).join('');
    return `
      <div class="ez-budget-row">
        <select class="ez-input" id="ez-alert-item"><option value="">Choose item…</option>${opts}${players}</select>
        <input class="ez-input" id="ez-alert-price" type="number" min="0" step="50" placeholder="Target price" aria-label="Alert target price">
        <button class="ez-btn primary" id="ez-add-alert">Add alert</button>
      </div>
      <div class="ez-alert-list" id="ez-alert-list"></div>
      <div class="ez-disclaimer">Alerts use stored console prices and are checked while this page is open. They stay in this browser.</div>`;
  }

  function metaNote(note) {
    const m = /^Meta (\d+) at (\w+): the best Ezzcoins meta rating for up to (\S+)$/.exec(note || '');
    return m ? `<div class="ez-player-note">Meta ${esc(m[1])} · best up to ${esc(m[3])}</div>` : '';
  }
  function playerHTML() {
    const meta = state.snapshot?.meta || [];
    if (!meta.length) return '<p class="ez-card-sub">No player quotes available yet.</p>';
    return `<div class="ez-player-grid">${meta.slice(0,8).map((p,i)=>{
      const asset = p.eaId ? window.EzzcoinsCardArt?.get(p.eaId,p.eaId,false) : null;
      const art = asset ? window.EzzcoinsCardArt.html(asset,'ez-player-render',p.name) : `<div class="ez-player-rating">${esc(p.ovr)}</div>`;
      return `<article class="ez-player" role="button" tabindex="0" aria-label="View ${esc(p.name)}" data-ez-player="${i}">
        <div class="ez-player-art">${art}</div><div class="ez-player-top"><span class="ez-pill watch">${esc(p.pos || '')}</span><span class="ez-player-source">${esc(p.priceSrc || 'No quote')}</span></div>
        <div class="ez-player-name">${esc(p.name)}</div>${metaNote(p.note)}<div class="ez-player-price">${coinPrice(p.price)} <small>${validPrice(p.price)?'coins':'unavailable'}</small></div>
        <div class="ez-player-meta">${esc(humanTime(p.priceAt))}</div></article>`;
    }).join('')}</div>`;
  }

  function playbookHTML() {
    const items = [
      ['The 84 floor','Use the Fodder board, not a fixed assumption. When ratings are within <strong>0.1 coins per Item Score point</strong>, treat them as a tie. Floor cards are often better for SBC use than taxable flips.'],
      ['Thursday dip → Friday flip','Rivals rewards add supply. Watch the live floor and meta prices, buy only when the price setup is there, then reassess before the Friday promo window.'],
      ['Midweek specials','Specials can soften Monday–Wednesday. Avoid treating a calendar pattern as enough on its own; confirm with the current price trend and upcoming content.'],
      ['Promo-night rule','Avoid chasing fresh promo cards in the first hour. Supply is usually highest just after packs open, so let the first listings settle.'],
      ['Low-budget bidding','Bid below the lowest Buy Now and use the Flip calculator to make sure the post-tax margin is worth it.'],
      ['Gallery hype','Gallery sets do not remove cards; SBCs do. Prefer demand that actually removes supply, and avoid holding after a collecting-only spike.']
    ];
    return items.map(([t,b],i)=>`<div class="ez-strategy ${i===0?'open':''}"><button type="button"><span>${t}</span><span>+</span></button><div class="ez-strategy-body">${b}</div></div>`).join('');
  }

  function shellHTML() {
    return `${heroHTML()}
      <div class="ez-grid">
        <section class="ez-card wide" id="ez-trades"><h3>Trade calls</h3><div class="ez-card-sub">Live calls from the latest market read. Confidence is not a win chance.</div>${tradesHTML()}</section>
        <section class="ez-card" id="ez-record"><h3>Track record</h3><div class="ez-card-sub">Only graded calls count</div>${trackHTML()}</section>
        <section class="ez-card wide" id="ez-drop"><h3>6 PM daily drop</h3><div class="ez-card-sub">How prices moved around EA's recent content drops, measured by Ezzcoins</div>${dropHTML()}</section>
        <section class="ez-card" id="ez-fodder"><h3>Best fodder value</h3><div class="ez-card-sub">Coins per Item Score point</div>${fodderHTML()}</section>
        <section class="ez-card wide" id="ez-budget"><h3>My Coins</h3><div class="ez-card-sub">Turn the current market read into a budget plan</div>${budgetHTML()}</section>
        <section class="ez-card" id="ez-coach"><h3>Coach shortcuts</h3><div class="ez-card-sub">One tap instead of thinking of a prompt</div>${coachHTML()}</section>
        <section class="ez-card full" id="ez-players"><h3>Meta cards to trade</h3><div class="ez-card-sub">The best meta card at each budget. Tap a card for details.</div>${playerHTML()}</section>
        <section class="ez-card half" id="ez-alerts"><h3>Price alerts</h3><div class="ez-card-sub">Saved in this browser</div>${alertsHTML()}</section>

      </div>`;
  }


  function showSection(id) {
    const target=document.getElementById(id);
    const panel=target?.closest('[role="tabpanel"]');
    if(panel) document.getElementById('tab-'+panel.id)?.click();
    target?.scrollIntoView({behavior:'smooth',block:'start'});
  }
  function meterHTML() {
    const p = state.pulse?.momentum != null ? state.pulse : state.snapshot?.index;
    const mom = Number(p?.momentum);
    if (!Number.isFinite(mom)) return '';
    const label = p.momentumLabel || (mom < 45 ? 'Prices are falling' : mom > 55 ? 'Prices are rising' : 'Prices are steady');
    const tone = mom < 45 ? 'down' : mom > 55 ? 'up' : 'flat';
    return `<div class="tx-meter" data-tone="${tone}">
      <div class="tx-meter-read"><strong>${Math.round(mom)}</strong><span><b>${esc(label)}</b>Share of moving cards that rose in the last hour</span></div>
      <div class="tx-meter-scale" role="img" aria-label="Market momentum ${Math.round(mom)} out of 100: ${esc(label)}">
        <div class="tx-meter-track"><span class="tx-meter-mark" style="left:${clamp(mom,0,100)}%"></span></div>
        <div class="tx-meter-ends" aria-hidden="true"><span>Falling</span><span>Steady</span><span>Rising</span></div>
      </div></div>`;
  }

  const TX_LAYOUT = `
    <div class="tx-hero" id="tx-hero"><div id="tx-board"></div><div id="tx-meter"></div></div>
    <nav class="tx-jump" aria-label="Trading sections">
      <button type="button" data-tx-go="tx-calls">Trade calls</button>
      <button type="button" data-tx-go="tx-drop">6 PM drop</button>
      <button type="button" data-tx-go="tx-fodder">Fodder</button>
      <button type="button" data-tx-go="tx-movers">Movers</button>
      <button type="button" data-tx-go="tx-players">Meta cards</button>
      <button type="button" data-tx-go="tx-alerts">Price alerts</button>
      <button type="button" class="tx-jump-plan" data-tx-plan>Plan my coins</button>
    </nav>
    <div class="tx-row tx-split"><div class="tx-slot" id="tx-calls"></div><div class="tx-slot" id="tx-record"></div></div>
    <div class="tx-row"><div class="tx-slot" id="tx-drop"></div></div>
    <div class="tx-row tx-split tx-narrow-first"><div class="tx-slot" id="tx-fodder"></div><div class="tx-slot" id="tx-movers"></div></div>
    <div class="tx-row"><div class="tx-slot" id="tx-players"></div></div>
    <div class="tx-row tx-split tx-even"><div class="tx-slot" id="tx-chart"></div><div class="tx-slot" id="tx-pulse"></div></div>
    <div class="tx-row"><div class="tx-slot" id="tx-alerts"></div></div>
    <div class="tx-row"><div class="tx-slot" id="tx-history"></div></div>
    <div id="tx-spare" hidden></div>`;

  function arrangeTrading() {
    const trading = document.getElementById('trading'); if (!trading) return;
    const byId = id => document.getElementById(id);
    const cardOf = id => byId(id)?.closest('.card');
    let layout = byId('tx-layout');
    if (!layout) {
      layout = document.createElement('div'); layout.id = 'tx-layout'; layout.innerHTML = TX_LAYOUT;
      trading.prepend(layout);
      // Static cards keep their ids, so the page's own updater keeps filling them in their new places.
      const once = [['tx-board', byId('readHead')?.closest('.board')], ['tx-fodder', cardOf('fodderTbl')], ['tx-chart', cardOf('chart')],
                    ['tx-movers', cardOf('fallers')], ['tx-pulse', cardOf('pulse')], ['tx-history', byId('record')]];
      for (const [slot, el] of once) if (el) byId(slot).append(el);
      for (const el of [cardOf('moves'), cardOf('metaTbl')]) if (el) byId('tx-spare').append(el);
      for (const g of [...trading.children]) if (g.classList.contains('grid2') && !g.children.length) g.remove();
      const ad = trading.querySelector(':scope > .ezz-ad'); if (ad) trading.append(ad);
    }
    // Fresh dashboard sections replace the previous ones on every refresh.
    const dyn = [['tx-calls','ez-trades'],['tx-record','ez-record'],['tx-drop','ez-drop'],['tx-players','ez-players'],['tx-alerts','ez-alerts']];
    for (const [slot] of dyn) byId(slot).replaceChildren();
    for (const [slot, id] of dyn) { const el = byId(id); if (el) byId(slot).append(el); }
    const when = byId('metaWhen')?.textContent.trim(), sub = byId('ez-players')?.querySelector('.ez-card-sub');
    if (when && sub) sub.insertAdjacentHTML('afterend', `<p class="tx-window">${esc(when)}</p>`);
    byId('tx-meter').innerHTML = meterHTML();
    const root = byId('ezz-upgrade-root'); if (root) trading.append(root);
  }

  function arrangeSections() {
    // Rebuild the managed groups on refresh, then move fresh nodes into their tabs.
    document.querySelectorAll('[data-ez-group]').forEach(el=>el.remove());
    const tools=document.getElementById('tools');
    if(tools){const group=document.createElement('div');group.className='ez-grid';group.dataset.ezGroup='tools';
      for(const id of ['ez-budget','ez-coach']){const el=document.getElementById(id);if(el)group.append(el);}
      tools.prepend(group);}
    arrangeTrading();
  }

  function findCoachInput() {
    const candidates = $$('textarea, input[type="text"], input:not([type])');
    return candidates.find(el => /message|coach|ask|trading/i.test(`${el.placeholder||''} ${el.getAttribute('aria-label')||''} ${el.name||''} ${el.id||''}`)) || null;
  }

  function coachPrompt(prompt) {
    const input = findCoachInput();
    if (input) {
      const panel = input.closest("section[id], [role=tabpanel]");
      if (panel?.hidden) document.getElementById("tab-" + panel.id)?.click();
      input.focus(); input.value = prompt; input.dispatchEvent(new Event('input',{bubbles:true}));
      $('#ez-coach-status').textContent = 'Prompt loaded into Coach — press Send.';
      input.scrollIntoView({behavior:'smooth',block:'center'});
      return;
    }
    const moves = state.snapshot?.moves || [];
    const relevant = /sell/i.test(prompt) ? moves.filter(m => /fodder/i.test(m.title + ' ' + m.detail) || m.tone === 'sell')
      : /event/i.test(prompt) ? moves.filter(m => m.when)
      : /buy|under/i.test(prompt) ? moves.filter(m => m.tone === 'buy')
      : moves;
    const answer = relevant.length ? relevant.map(m => replaceTimeTokens(m.title + ': ' + m.detail)).join('\n\n')
      : 'There are no confirmed BUY calls in this market read. Keep coins available and wait for the next update.';
    $('#ez-coach-status').textContent = (!isFresh() ? ageNote() + '\n\n' : '') + answer;
  }

  function alertLabel(key) {
    if (key.startsWith('fodder:')) return `${key.split(':')[1]}-rated fodder`;
    if (key.startsWith('player:')) return key.slice(7);
    return key;
  }

  function currentPrice(key) {
    if (key.startsWith('fodder:')) {
      const ovr = Number(key.split(':')[1]); return (state.snapshot?.fodder || []).find(x => +x.ovr === ovr)?.price ?? null;
    }
    if (key.startsWith('player:')) {
      const name = key.slice(7); return (state.snapshot?.meta || []).find(x => x.name === name)?.price ?? null;
    }
    return null;
  }

  function quoteFresh(key) {
    const at = key.startsWith('player:') ? (state.snapshot?.meta || []).find(p => 'player:'+p.name === key)?.priceAt : state.snapshot?.updatedAt;
    return window.EzzcoinsMarket.freshness(at).usable;
  }
  function alertReached(a) {
    const p = currentPrice(a.key);
    return quoteFresh(a.key) && validPrice(p) && +p <= +a.target;
  }

  function renderAlerts() {
    const box = $('#ez-alert-list'); if (!box) return;
    const alerts = savedAlerts();
    if (!alerts.length) { box.innerHTML = '<div style="font-size:12px;color:var(--ez-muted)">No alerts yet.</div>'; return; }
    box.innerHTML = alerts.map((a,i) => {
      const now = currentPrice(a.key); const hit = alertReached(a);
      return `<div class="ez-alert-item"><div><strong class="${hit?'ez-positive':''}">${esc(alertLabel(a.key))}</strong><small>${hit?'Target reached':'Target'}: ${coinPrice(a.target)}${validPrice(now)?` · stored ${coinPrice(now)}`: ' · price unavailable'}${!quoteFresh(a.key) ? ' · waiting for fresh quote' : ''}</small></div><button class="ez-icon-btn" data-ez-remove-alert="${i}" aria-label="Remove alert">×</button></div>`;
    }).join('');
  }

  function checkAlerts() {
    const alerts = savedAlerts();
    const hits = alerts.filter(alertReached);
    if (hits.length) toast(`${hits.length} Ezzcoins price alert${hits.length>1?'s':''} reached`);
  }

  function addAlert() {
    const key = $('#ez-alert-item')?.value; const target = Number($('#ez-alert-price')?.value);
    if (!key || !Number.isFinite(target) || target <= 0) return toast('Choose an item and target price');
    const alerts = savedAlerts();
    alerts.push({key,target,createdAt:new Date().toISOString()});
    saveJSON(STORAGE.alerts, alerts.slice(-30)); renderAlerts(); checkAlerts();
    $('#ez-alert-price').value=''; toast('Alert saved');
  }

  function openPlayer(index) {
    const p = state.snapshot?.meta?.[index]; if (!p) return;
    const modal = $('#ez-player-modal');
    const mover = [...(state.snapshot?.fallers||[]),...(state.snapshot?.risers||[])].find(x => x.name.toLowerCase() === p.name.toLowerCase());
    modal.querySelector('.ez-modal-content').innerHTML = `
      <div class="ez-kicker">${esc(p.pos || 'Player')} · ${esc(p.ovr || '')} OVR</div>
      <h3>${esc(p.name)}</h3>
      <div class="ez-metric">${coinPrice(p.price)}</div><div class="ez-metric-label">Console quote · ${esc(p.priceSrc || 'Unavailable')} · ${esc(humanTime(p.priceAt))}</div>
      ${mover ? `<div class="ez-mini-row"><span>Today</span><span class="${mover.pct>=0?'ez-positive':'ez-danger'}">${mover.pct>=0?'+':''}${mover.pct}%</span></div>`:''}
      <p>${esc(p.note || 'No extra note in the current snapshot.')}</p>
      <button class="ez-btn primary" data-ez-modal-alert="${esc(p.name)}">Create price alert</button>
      <div class="ez-disclaimer">For full stats, chemistry styles and every card version, use the existing Ezzcoins player database.</div>`;
    modal._trigger = document.activeElement;
    modal.classList.add('open');
    modal.querySelector('.ez-modal-close').focus();
  }

  function closePlayer() {
    const modal = $('#ez-player-modal');
    modal.classList.remove('open');
    modal._trigger?.focus();
  }

  function bind() {
    $$('[data-ez-budget]').forEach(b => b.addEventListener('click', () => { $('#ez-budget-input').value = b.dataset.ezBudget; renderAllocation(); }));
    $('[data-ez-record]')?.addEventListener('click', () => { $('#tab-trading')?.click(); const record = $('#record'); if (record) { record.open = true; record.scrollIntoView({behavior:'smooth',block:'start'}); } });
    $$('[data-ez-scroll]').forEach(btn => btn.addEventListener('click', () => showSection(`ez-${btn.dataset.ezScroll}`)));
    $('#ez-plan-btn')?.addEventListener('click', renderAllocation);
    $('#ez-budget-input')?.addEventListener('keydown', e => { if(e.key==='Enter') renderAllocation(); });
    $$('[data-ez-prompt]').forEach(b => b.addEventListener('click', ()=>coachPrompt(b.dataset.ezPrompt)));
    $('#ez-add-alert')?.addEventListener('click', addAlert);
    $('#ez-alert-item')?.addEventListener('change', e => {
      const opt = e.target.selectedOptions?.[0]; if (opt?.dataset.price) $('#ez-alert-price').value = opt.dataset.price;
    });
    $('#ez-alert-list')?.addEventListener('click', e => {
      const b = e.target.closest('[data-ez-remove-alert]'); if (!b) return;
      const alerts=savedAlerts(); alerts.splice(Number(b.dataset.ezRemoveAlert),1); saveJSON(STORAGE.alerts,alerts); renderAlerts();
    });
    $$('.ez-strategy button').forEach(b=>{ b.setAttribute('aria-expanded', b.closest('.ez-strategy').classList.contains('open')); b.addEventListener('click',()=>{ const open=b.closest('.ez-strategy').classList.toggle('open'); b.setAttribute('aria-expanded', open); }); });
    $$('.ez-player').forEach(p=>p.addEventListener('click',()=>openPlayer(Number(p.dataset.ezPlayer))));
    $$('.ez-player').forEach(p=>p.addEventListener('keydown',e=>{ if(e.key==='Enter'||e.key===' ') { e.preventDefault(); openPlayer(Number(p.dataset.ezPlayer)); } }));
  }

  function bindModal() {
    $('#ez-player-modal')?.addEventListener('click',e=>{ if(e.target.matches('.ez-modal-backdrop,.ez-modal-close')) closePlayer(); });
    $('#ez-player-modal')?.addEventListener('click',e=>{
      const b=e.target.closest('[data-ez-modal-alert]'); if(!b) return;
      closePlayer();
      showSection('ez-alerts');
      const sel=$('#ez-alert-item'); if(sel){ sel.value=`player:${b.dataset.ezModalAlert}`; sel.dispatchEvent(new Event('change',{bubbles:true})); }
    });
    document.addEventListener('keydown',e=>{
      const modal=$('#ez-player-modal'); if(!modal?.classList.contains('open')) return;
      if(e.key==='Escape') closePlayer();
      if(e.key==='Tab') {
        const focusable=$$('button, a[href], input, select, [tabindex="0"]',modal);
        const first=focusable[0], last=focusable.at(-1);
        if(e.shiftKey && document.activeElement===first) { e.preventDefault(); last.focus(); }
        else if(!e.shiftKey && document.activeElement===last) { e.preventDefault(); first.focus(); }
      }
    });
  }

  function injectModal() {
    const modal = document.createElement('div'); modal.id='ez-player-modal'; modal.className='ez-modal-backdrop';
    modal.innerHTML='<div class="ez-modal" role="dialog" aria-modal="true" aria-label="Player details"><div class="ez-modal-head"><div class="ez-modal-content"></div><button class="ez-modal-close" aria-label="Close">×</button></div></div>';
    document.body.appendChild(modal);
    bindModal();
  }

  let refreshing = false;
  async function refresh() {
    if (refreshing) return;
    refreshing = true;
    try {
      await loadData();
      const root=$('#ezz-upgrade-root');
      const input=$('#ez-budget-input');
      if(input && Number.isFinite(Number(input.value))) saveJSON(STORAGE.budget, Number(input.value));
      if($('#ez-player-modal')?.classList.contains('open')) closePlayer();
      root.innerHTML=shellHTML();
      arrangeSections(); bind(); renderAllocation(); renderAlerts(); checkAlerts();
    } finally { refreshing=false; }
  }

  async function init() {
    if ($('#ezz-upgrade-root')) return;
    await loadData();
    const root = document.createElement('div'); root.id='ezz-upgrade-root'; root.innerHTML=shellHTML();
    const {parent,before}=findInsertionPoint(); parent.insertBefore(root,before);
    injectModal(); arrangeSections(); bind(); renderAllocation(); renderAlerts(); checkAlerts();
    document.addEventListener('click', e => {
      const more = e.target.closest('.ez-trade-more');
      if (more) { const open = more.closest('.ez-trade').classList.toggle('open'); more.setAttribute('aria-expanded', open); more.textContent = open ? 'Show less' : 'Show why'; return; }
      const go = e.target.closest('[data-tx-go]');
      if (go) { document.getElementById(go.dataset.txGo)?.scrollIntoView({behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start'}); return; }
      if (e.target.closest('[data-tx-plan]')) showSection('ez-budget');
    });
    $('#refreshBtn')?.addEventListener('click', refresh);
    setInterval(refresh, 60000);
    // The drop clock ticks between data refreshes.
    setInterval(() => { if (!document.hidden) $$('[data-ez-drop-clock]').forEach(el => { el.innerHTML = clockHTML(); }); }, 20000);
    document.addEventListener('visibilitychange', () => { if(!document.hidden) refresh(); });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, {once:true}); else init();
})();


