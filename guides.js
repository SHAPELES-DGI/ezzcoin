/* © 2026 Ezzcoins. All rights reserved. Live panels on the trading guide pages. */
(() => {
  'use strict';
  const M = window.EzzcoinsMarket;
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const coins = n => Number.isFinite(+n) ? Math.round(+n).toLocaleString('en-US') : '–';
  const pct = v => v == null || !Number.isFinite(+v) ? '–' : (+v > 0 ? '+' : '') + (+v).toFixed(1) + '%';
  const tone = v => +v > 1 ? 'up' : +v < -1 ? 'down' : '';
  const ago = iso => { const m = Math.round((Date.now() - Date.parse(iso)) / 60000); return !Number.isFinite(m) ? '' : m < 2 ? 'just now' : m < 60 ? m + ' min ago' : Math.round(m / 60) + ' h ago'; };
  const when = ms => new Date(ms).toLocaleString([], {weekday:'short', hour:'2-digit', minute:'2-digit'});
  const span = ms => { const m = Math.max(0, Math.round(ms / 60000)), h = Math.floor(m / 60), d = Math.floor(h / 24);
    return d ? `${d}d ${h % 24}h` : h ? `${h}h ${String(m % 60).padStart(2, '0')}m` : `${m}m`; };
  const tokens = t => String(t || '').replace(/\{\{t:([^}]+)\}\}/g, (_, iso) => Number.isNaN(Date.parse(iso)) ? '' : when(Date.parse(iso)));

  // UK wall-clock times, so countdowns are right in any time zone and across clock changes.
  const UK = new Intl.DateTimeFormat('en-GB', {timeZone:'Europe/London', year:'numeric', month:'numeric', day:'numeric', hour:'numeric', minute:'numeric', second:'numeric', hourCycle:'h23'});
  const ukParts = ms => { const p = {}; for (const {type, value} of UK.formatToParts(new Date(ms))) p[type] = +value; return p; };
  const ukWall = (y, m, d, h) => { const g = Date.UTC(y, m - 1, d, h), p = ukParts(g); return g - (Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute, p.second) - g); };
  function nextUk(weekday, hour) {   // weekday: 0 = Sunday … 5 = Friday
    const now = Date.now(), p = ukParts(now);
    for (let i = 0; i < 8; i++) {
      const t = ukWall(p.year, p.month, p.day + i, hour), q = ukParts(t);
      if (new Date(Date.UTC(q.year, q.month - 1, q.day)).getUTCDay() === weekday && t > now) return t;
    }
    return null;
  }

  const STATUS = {active: 'Active', retest: 'Retest after a pause', new: 'Untested so far', paused: 'Paused', off: 'Off: loses in the paper test'};
  function strategy(ledger, key) {
    const b = (ledger?.strategyBoard || []).find(x => x.key === key);
    if (!b) return '';
    const n = (+b.hit || 0) + (+b.miss || 0);
    const line = (n ? `${b.hit} of ${n} graded calls hit, ${pct(b.avg)} on average after the 5% tax.` : 'No graded calls yet: the first ones are graded automatically at their check time.')
      + (b.test && +b.test.n ? ` Replayed on recently recorded prices: ${b.test.hit} of ${b.test.n} paper calls hit, ${pct(b.test.avg)} on average.` : '');
    return `<div class="strat"><div class="strat-top"><b>${esc(b.name)}</b><span class="pill ${esc(b.status)}">${esc(STATUS[b.status] || b.status)}</span></div><p>${esc(line)}</p></div>`;
  }

  const render = {
    fodder(s) {
      const rows = (s?.fodder || []).filter(r => r.price > 0 && r.score > 0).map(r => ({...r, cpp: r.price / r.score}));
      if (!rows.length) return '<p class="muted">The fodder board is waiting for fresh prices.</p>';
      const best = Math.min(...rows.map(r => r.cpp));
      return `<table><thead><tr><th>Rating</th><th>Cheapest</th><th>Item Score</th><th>Coins per point</th></tr></thead><tbody>${rows.map(r =>
        `<tr class="${r.cpp - best < 0.1 ? 'best' : ''}"><td>${r.ovr}</td><td>${coins(r.price)}</td><td>${coins(r.score)}</td><td>${r.cpp.toFixed(2)}${r.cpp - best < 0.1 ? ' <span class="tag-best">best</span>' : ''}</td></tr>`).join('')}</tbody></table>
        <p class="muted">Console prices, read ${esc(ago(s.pricesUpdatedAt || s.updatedAt))}. Ratings within 0.1 coins per point of the cheapest count as a tie.</p>`;
    },
    rewards(s, l) {
      const ev = (s?.events || []).find(e => e.title === 'Rivals rewards'), t = ev ? Date.parse(ev.date) : NaN;
      const next = Number.isFinite(t) && t > Date.now() ? `<p class="big">${span(t - Date.now())}</p><p class="muted">until the next Rivals rewards, ${esc(when(t))} your time.</p>` : '<p class="muted">Rivals rewards pay out on Thursday morning, UK time.</p>';
      return next + strategy(l, 'rewards');
    },
    weekend(s, l) {
      const fri = nextUk(5, 20);
      return (fri ? `<p class="big">${span(fri - Date.now())}</p><p class="muted">until this week's calls are checked: Friday 8 PM UK, ${esc(when(fri))} your time.</p>` : '')
        + strategy(l, 'weekend') + (s?.verdict?.label ? `<p class="muted">Market right now: ${esc(s.verdict.label.toLowerCase())}.</p>` : '');
    },
    promo(s) {
      const d = s?.dailyDrop, fri = nextUk(5, 18);
      let out = fri ? `<p class="big">${span(fri - Date.now())}</p><p class="muted">until Friday's 6 PM UK drop, ${esc(when(fri))} your time.</p>` : '';
      if (!d) return out + '<p class="muted">The drop record appears with the next market read.</p>';
      out += `<p>${esc(tokens(d.fodder?.text))}</p>`;
      const rec = (d.recent || []).slice(0, 7);
      if (rec.length) out += `<table><thead><tr><th>Evening</th><th>84s</th><th>85s</th><th>86s</th><th>Top 100</th></tr></thead><tbody>${rec.map(r =>
        `<tr class="${r.friday ? 'best' : ''}"><td>${esc(new Date(r.date + 'T12:00:00Z').toLocaleDateString([], {weekday:'short', day:'numeric', month:'short'}))}${r.friday ? ' <span class="tag-best">Friday</span>' : ''}</td>${['f84','f85','f86','i100'].map(k => `<td class="${tone(r.chg?.[k])}">${pct(r.chg?.[k])}</td>`).join('')}</tr>`).join('')}</tbody></table>
        <p class="muted">Change from just before 6 PM to about 8 PM UK. ${esc(d.measured)} evenings measured so far.</p>`;
      return out;
    },
    hype(s, l) {
      const r = (s?.risers || []).slice(0, 5);
      const list = r.length ? `<ol class="movers">${r.map(x => `<li><span>${esc(x.name)} ${esc(x.ovr ?? '')} <small>${esc(x.version && x.version !== 'Rare' ? x.version : '')}</small></span><b class="up">${pct(x.pct)}</b></li>`).join('')}</ol>
        <p class="muted">Cards worth 5,000+ coins, against the price about a day ago.</p>` : '<p class="muted">No big risers in the latest read.</p>';
      return list + strategy(l, 'fade');
    }
  };

  // Profit after tax: the same maths and price steps as the Ezzcoins flip calculator.
  const STEPS = [[1e3, 50], [1e4, 100], [5e4, 250], [1e5, 500], [Infinity, 1e3]];
  const stepUp = v => { const s = STEPS.find(([t]) => v < t)[1]; return Math.ceil(v / s) * s; };
  function calc(box) {
    box.innerHTML = `<div class="calc"><label>Buy price<input type="number" inputmode="numeric" min="0" step="50" value="10000" data-c="buy"></label>
      <label>Sell price<input type="number" inputmode="numeric" min="0" step="50" value="11000" data-c="sell"></label></div><div class="calc-out" aria-live="polite"></div>
      <p class="muted">You receive the sale price × 0.95, rounded down. Break-even is rounded up to the market's price steps.</p>`;
    const out = box.querySelector('.calc-out');
    const update = () => {
      const buy = Math.max(0, +box.querySelector('[data-c=buy]').value || 0), sell = Math.max(0, +box.querySelector('[data-c=sell]').value || 0);
      const get = Math.floor(sell * 0.95), profit = get - buy;
      out.innerHTML = `<div><span>You receive</span><b>${coins(get)}</b></div><div><span>Profit</span><b class="${profit >= 0 ? 'up' : 'down'}">${profit >= 0 ? '+' : ''}${coins(profit)}</b></div>
        <div><span>Break-even sell price</span><b>${buy ? coins(stepUp(buy / 0.95)) : '–'}</b></div>`;
    };
    box.addEventListener('input', update); update();
  }

  async function fill() {
    const live = [...document.querySelectorAll('[data-live]')].filter(b => b.dataset.live !== 'calc');
    if (!live.length || !M) return;
    const [s, l] = await Promise.all(['snapshot.json', 'ledger.json'].map(n => M.fetchData(n).catch(() => null)));
    for (const b of live) {
      const body = b.querySelector('.live-body');
      try { body.innerHTML = s || l ? render[b.dataset.live](s, l) : '<p class="muted">Live data could not be loaded. Try again in a minute.</p>'; }
      catch (_) { body.innerHTML = '<p class="muted">Live data could not be shown.</p>'; }
    }
  }
  function init() {
    for (const b of document.querySelectorAll('[data-live="calc"]')) calc(b.querySelector('.live-body'));
    fill();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, {once: true}); else init();
  setInterval(() => { if (!document.hidden) fill(); }, 120000);
})();
