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

  const state = { snapshot: null, ledger: null, history: null };
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  const esc = s => String(s ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  const validPrice = n => n != null && n !== '' && Number.isFinite(+n) && +n > 0;
  const coins = n => n != null && n !== '' && Number.isFinite(+n) ? new Intl.NumberFormat().format(Math.round(+n)) : '—';
  const clamp = (n,a,b) => Math.max(a,Math.min(b,n));
  const toneClass = tone => ['buy','sell','watch','hold'].includes(tone) ? tone : 'watch';
  const confidenceIndex = c => CONFIDENCE_INDEX[String(c || '').toLowerCase()] || 35;
  const getJSON = (key, fallback) => { try { return JSON.parse(localStorage.getItem(key) || '') || fallback; } catch { return fallback; } };
  const saveJSON = (key, value) => { try { localStorage.setItem(key, JSON.stringify(value)); } catch { toast('Browser storage is unavailable; this change will not persist.'); } };
  const savedAlerts = () => { const a = getJSON(STORAGE.alerts, []); return Array.isArray(a) ? a.filter(x => x && typeof x.key === 'string' && validPrice(x.target)) : []; };
  const isFresh = () => { const t = Date.parse(state.snapshot?.updatedAt); return Number.isFinite(t) && Date.now() - t >= 0 && Date.now() - t <= 3 * 3600e3; };

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
    const bust = `?v=${Date.now()}`;
    const urls = ['data/snapshot.json','data/ledger.json','data/history.json'];
    const results = await Promise.allSettled(urls.map(u => fetch(u + bust, {cache:'no-store'}).then(r => {
      if (!r.ok) throw new Error(`${u}: ${r.status}`); return r.json();
    })));
    if (results[0].status === 'fulfilled') state.snapshot = results[0].value;
    if (results[1].status === 'fulfilled') state.ledger = results[1].value;
    if (results[2].status === 'fulfilled') state.history = results[2].value;
    return results.some(r => r.status === 'fulfilled');
  }

  function gradedStats() {
    const calls = state.ledger?.calls || [];
    const graded = calls.filter(c => c.status === 'hit' || c.status === 'miss');
    const hits = graded.filter(c => c.status === 'hit');
    const resultVals = graded.filter(c => c.tone === 'buy' && c.result != null && c.result !== '').map(c => Number(c.result)).filter(Number.isFinite);
    return {
      graded: graded.length,
      hits: hits.length,
      winRate: graded.length ? (hits.length / graded.length * 100) : null,
      avg: resultVals.length ? resultVals.reduce((a,b)=>a+b,0)/resultVals.length : null
    };
  }

  function bestFodder() {
    const f = (state.snapshot?.fodder || []).map(x => ({...x, cpp: validPrice(x.price) && x.score > 0 ? x.price/x.score : Infinity})).filter(x => Number.isFinite(x.cpp));
    if (!f.length) return null;
    f.sort((a,b)=>a.cpp-b.cpp);
    const best = f[0], near = f.filter(x => x.cpp - best.cpp < .1);
    return {best, near};
  }

  function heroHTML() {
    const s = state.snapshot;
    const v = s?.verdict || {};
    const stale = !isFresh();
    return `
      <section class="ez-hero">
        <div class="ez-hero-top">
          <div>
            <div class="ez-kicker">Ezzcoins Command Center</div>
            <h2>${esc(v.label || 'Waiting for the latest market read')}</h2>
            <p>${esc(replaceTimeTokens(v.detail || 'Market data is unavailable. Try Refresh again shortly.'))}</p>
          </div>
          <div class="ez-status"><span class="ez-dot ${!stale?'is-live':''}"></span>${esc(humanTime(s?.updatedAt))}${stale ? ' · stale' : ''}</div>
        </div>
        <div class="ez-actions">
          <button class="ez-btn primary" data-ez-scroll="trades">Best trades now</button>
          <button class="ez-btn" data-ez-scroll="budget">Plan my coins</button>
          <button class="ez-btn ghost" data-ez-scroll="alerts">Price alerts</button>
          <button class="ez-btn ghost" data-ez-scroll="coach">Ask Coach</button>
        </div>
      </section>`;
  }

  function tradesHTML() {
    const moves = state.snapshot?.moves || [];
    if (!moves.length) return '<p class="ez-card-sub">No market calls available yet.</p>';
    return `<div class="ez-trades">${moves.slice(0,4).map((m,i) => {
      const idx = confidenceIndex(m.confidence);
      return `<article class="ez-trade">
        <div class="ez-trade-head"><div class="ez-trade-title">${esc(m.title)}</div><span class="ez-pill ${toneClass(m.tone)}">${esc(m.tone || 'watch')}</span></div>
        <p>${esc(replaceTimeTokens(m.detail))}</p>
        <div class="ez-trade-foot">
          <span>${esc(replaceTimeTokens(m.when || 'Current update'))}</span>
          <span class="ez-confidence" title="Internal confidence index, not a win probability">${esc(m.confidence || 'low')} <span class="ez-confbar"><i style="width:${idx}%"></i></span> ${idx}/100</span>
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
      <div class="ez-metric-label">graded-call win rate</div>
      <div class="ez-mini-row"><span>Graded calls</span><span>${st.graded}</span></div>
      <div class="ez-mini-row"><span>Hits</span><span>${st.hits}</span></div>
      <div class="ez-mini-row"><span>Avg BUY return after tax</span><span>${avg}</span></div>
      <button class="ez-btn ghost" data-ez-record>Open full history</button>
      <div class="ez-disclaimer">Voided or pending calls are excluded. Grading stays based on your existing ledger rules.</div>`;
  }

  function fodderHTML() {
    const b = bestFodder();
    if (!b) return '<div class="ez-skeleton"></div>';
    const tie = b.near.length > 1;
    return `
      <div class="ez-metric">${tie ? b.near.map(x=>x.ovr).join('–') : b.best.ovr}</div>
      <div class="ez-metric-label">best Item Score value ${tie ? '(near-tie)' : ''}</div>
      <div class="ez-mini-row"><span>Lowest c / pt</span><span>${b.best.cpp.toFixed(2)}</span></div>
      <div class="ez-mini-row"><span>${b.best.ovr} floor</span><span>${coins(b.best.price)}</span></div>
      <div class="ez-mini-row"><span>Score</span><span>${coins(b.best.score)}</span></div>`;
  }

  function allocationFor(budget) {
    if (!isFresh()) return [['Keep liquid', 100, 'Market data is stale or unavailable. Refresh before acting.']];
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
    $('#ez-allocation').innerHTML = plan.map(([label,pct,note]) => `
      <div class="ez-alloc"><span>${esc(label)}</span><span class="ez-alloc-bar"><i style="width:${pct}%"></i></span><strong>${coins(budget*pct/100)} (${pct}%)</strong></div>
      <div style="margin:-5px 0 6px 103px;font-size:10.5px;color:var(--ez-muted)">${esc(note)}</div>`).join('');
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

  function playerHTML() {
    const meta = state.snapshot?.meta || [];
    if (!meta.length) return '<p class="ez-card-sub">No player prices available yet.</p>';
    return `<div class="ez-player-grid">${meta.slice(0,8).map((p,i)=>`<article class="ez-player" role="button" tabindex="0" aria-label="View ${esc(p.name)}" data-ez-player="${i}"><div class="ez-player-top"><span class="ez-player-rating">${esc(p.ovr)}</span><span class="ez-pill watch">${esc(p.pos || '')}</span></div><div class="ez-player-name">${esc(p.name)}</div><div class="ez-player-meta">${esc(p.note || '')}</div><div class="ez-player-price">${coins(p.price)} coins</div></article>`).join('')}</div>`;
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
        <section class="ez-card wide" id="ez-trades"><h3>Best trades right now</h3><div class="ez-card-sub">Current stored calls · confidence index is not a win probability</div>${tradesHTML()}</section>
        <section class="ez-card"><h3>Track record</h3><div class="ez-card-sub">Only graded calls count</div>${trackHTML()}</section>
        <section class="ez-card" id="ez-fodder"><h3>Best fodder value</h3><div class="ez-card-sub">Coins per Item Score point</div>${fodderHTML()}</section>
        <section class="ez-card wide" id="ez-budget"><h3>My Coins</h3><div class="ez-card-sub">Turn the current market read into a budget plan</div>${budgetHTML()}</section>
        <section class="ez-card" id="ez-coach"><h3>Coach shortcuts</h3><div class="ez-card-sub">One tap instead of thinking of a prompt</div>${coachHTML()}</section>
        <section class="ez-card full" id="ez-players"><h3>Player trade board</h3><div class="ez-card-sub">Tap a card for a quick detail view; your existing player database still handles the full search</div>${playerHTML()}</section>
        <section class="ez-card half" id="ez-alerts"><h3>Price alerts</h3><div class="ez-card-sub">Saved in this browser</div>${alertsHTML()}</section>
        <section class="ez-card half"><h3>Quick Playbook</h3><div class="ez-card-sub">The long strategy guide, compressed</div>${playbookHTML()}</section>
      </div>`;
  }

  function findCoachInput() {
    const candidates = $$('textarea, input[type="text"], input:not([type])');
    return candidates.find(el => /message|coach|ask|trading/i.test(`${el.placeholder||''} ${el.getAttribute('aria-label')||''} ${el.name||''} ${el.id||''}`)) || null;
  }

  function coachPrompt(prompt) {
    const input = findCoachInput();
    if (input) {
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
    $('#ez-coach-status').textContent = (!isFresh() ? 'Stored data is stale. Refresh before acting.\n\n' : '') + answer;
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

  function alertReached(a) {
    const p = currentPrice(a.key);
    const older = /earlier update/i.test((state.snapshot?.meta || []).find(x => 'player:'+x.name === a.key)?.note || '');
    return isFresh() && !older && validPrice(p) && +p <= +a.target;
  }

  function renderAlerts() {
    const box = $('#ez-alert-list'); if (!box) return;
    const alerts = savedAlerts();
    if (!alerts.length) { box.innerHTML = '<div style="font-size:12px;color:var(--ez-muted)">No alerts yet.</div>'; return; }
    box.innerHTML = alerts.map((a,i) => {
      const now = currentPrice(a.key); const hit = alertReached(a);
      return `<div class="ez-alert-item"><div><strong class="${hit?'ez-positive':''}">${esc(alertLabel(a.key))}</strong><small>${hit?'Target reached':'Target'}: ${coins(a.target)}${validPrice(now)?` · stored ${coins(now)}`: ' · price unavailable'}${!isFresh() ? ' · waiting for fresh data' : ''}</small></div><button class="ez-icon-btn" data-ez-remove-alert="${i}" aria-label="Remove alert">×</button></div>`;
    }).join('');
  }

  function checkAlerts() {
    if (!isFresh()) return;
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
      <div class="ez-metric">${coins(p.price)}</div><div class="ez-metric-label">current stored console price</div>
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
    $$('[data-ez-scroll]').forEach(btn => btn.addEventListener('click', () => $(`#ez-${btn.dataset.ezScroll}`)?.scrollIntoView({behavior:'smooth',block:'start'})));
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
      $('#ez-alerts')?.scrollIntoView({behavior:'smooth',block:'center'});
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
      bind(); renderAllocation(); renderAlerts(); checkAlerts();
    } finally { refreshing=false; }
  }

  async function init() {
    if ($('#ezz-upgrade-root')) return;
    await loadData();
    const root = document.createElement('div'); root.id='ezz-upgrade-root'; root.innerHTML=shellHTML();
    const {parent,before}=findInsertionPoint(); parent.insertBefore(root,before);
    injectModal(); bind(); renderAllocation(); renderAlerts(); checkAlerts();
    $('#refreshBtn')?.addEventListener('click', refresh);
    setInterval(refresh, 5 * 60000);
    document.addEventListener('visibilitychange', () => { if(!document.hidden) refresh(); });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, {once:true}); else init();
})();
