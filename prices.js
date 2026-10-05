(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const number = value => value.toLocaleString('en-US');
  const escape = value => String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
  const normalize = value => String(value ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  let feed = null, cards = [], filtered = [], shown = 0, busy = false;
  const filterIds = ['search', 'platform', 'type', 'minRating', 'maxPrice', 'availability', 'sort'];
  const date = value => new Date(value).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZoneName: 'short' });
  const stateLabel = (card, platform) => {
    const quote = window.EzzcoinsMarket.lookup(feed, card.id, platform);
    if (!quote) return 'Not in market feed';
    if (quote.status === 0) return 'No listing recorded';
    return feed.statusLabels[String(quote.status)] || 'No market price';
  };
  function buildCards(roster, extras) {
    const cols = Object.fromEntries(roster.cols.map((col, i) => [col, i]));
    const byId = new Map(roster.rows.map(row => {
      const card = { id: +row[cols.id], name: row[cols.name], full: row[cols.full], rating: +row[cols.ovr],
        position: row[cols.pos], club: row[cols.club], nation: row[cols.nation], version: 'Base', type: 'base', url: 'https://www.fut.gg/players/' };
      return [card.id, card];
    }));
    const ec = Object.fromEntries(extras.cols.map((col, i) => [col, i]));
    for (const row of extras.rows) {
      const version = row[ec.version];
      const type = /icon/i.test(version) ? 'icon' : /hero/i.test(version) ? 'hero' : row[ec.id] === row[ec.baseId] ? 'base' : 'special';
      byId.set(row[ec.id], { id: row[ec.id], name: row[ec.name], rating: row[ec.ovr], position: row[ec.pos],
        club: row[ec.club], nation: row[ec.nation], version, type, url: row[ec.url] });
    }
    for (const row of feed.rows) if (!byId.has(row[0])) {
      byId.set(row[0], { id: row[0], name: 'Card details unavailable', rating: null, position: '', club: '', version: 'Exact item ID ' + row[0], type: 'unknown', url: 'https://www.fut.gg/players/' });
    }
    return [...byId.values()].map(card => ({ ...card, key: normalize([card.name, card.full, card.club, card.nation, card.version, card.id].join(' ')) }));
  }
  function freshness() {
    if (!feed) return;
    const platform = $('platform').value;
    const time = feed.publishedAt[platform];
    const minutes = Math.max(0, Math.floor((Date.now() - Date.parse(time)) / 60000));
    const delayed = minutes > 90;
    $('freshness').textContent = delayed ? 'Delayed prices' : 'Recent price feed';
    $('freshness').classList.toggle('stale', delayed);
    $('sourceTime').textContent = 'FUT.GG · ' + date(time);
    $('priceCount').textContent = number(platform === 'pc' ? feed.coverage.pcPriced : feed.coverage.consolePriced);
    $('platformLabel').textContent = (platform === 'pc' ? 'PC' : 'Console') + ' prices available';
    $('cardCount').textContent = number(feed.coverage.feedCards);
    const missing = feed.rows.filter(row => !cards.findCardIds.has(row[0])).length;
    $('notice').textContent = (delayed ? 'The source feed is ' + (minutes < 120 ? minutes + ' minutes' : Math.floor(minutes / 60) + ' hours') + ' old. Check the price in-game before buying. ' : 'Check the Transfer Market before buying; prices and availability can change. ') + (missing ? number(missing) + ' feed IDs have prices but no matching card details yet.' : 'All feed IDs have matching player/card details.');
    $('notice').classList.toggle('error', delayed);
  }
  function renderMore(reset = false) {
    if (reset) { shown = 0; $('results').replaceChildren(); }
    const platform = $('platform').value;
    const batch = filtered.slice(shown, shown + 50);
    $('results').insertAdjacentHTML('beforeend', batch.map(({ card, price }) => {
      const color = card.rating < 65 ? ' bronze' : card.rating < 75 ? ' silver' : '';
      return `<tr><td class="player"><strong>${escape(card.name)}</strong><small>${escape(card.version)} · ID ${card.id}</small></td><td>${card.rating ? `<span class="rating${color}">${card.rating}</span>` : '—'}</td><td>${escape(card.position || '—')}</td><td class="club">${escape(card.club || card.nation || '—')}</td><td class="price${price === null ? ' unavailable' : ''}">${price === null ? escape(stateLabel(card, platform)) : number(price)}</td><td><a class="source" href="${escape(card.url)}" target="_blank" rel="noopener noreferrer">FUT.GG ↗</a></td></tr>`;
    }).join(''));
    shown += batch.length;
    if (!filtered.length) $('results').innerHTML = '<tr><td colspan="6" class="empty">No cards match these filters. Try a different name, budget or availability.</td></tr>';
    $('shown').textContent = number(shown) + ' of ' + number(filtered.length) + ' results';
    $('more').hidden = shown >= filtered.length;
  }
  function applyFilters() {
    if (!feed) return;
    const platform = $('platform').value, type = $('type').value, availability = $('availability').value;
    const terms = normalize($('search').value.trim()).split(/\s+/).filter(Boolean);
    const minRating = Math.max(0, Number($('minRating').value) || 0);
    const budget = $('maxPrice').value === '' ? null : Math.max(0, Number($('maxPrice').value));
    filtered = cards.map(card => ({ card, price: window.EzzcoinsMarket.lookup(feed, card.id, platform)?.price ?? null })).filter(({ card, price }) =>
      terms.every(term => card.key.includes(term)) && (!type || card.type === type) && (card.rating ?? 0) >= minRating &&
      (budget === null || price !== null && price <= budget) && (availability === 'all' || (availability === 'priced' ? price !== null : price === null)));
    const sort = $('sort').value;
    filtered.sort((a, b) => {
      if (sort === 'name') return a.card.name.localeCompare(b.card.name) || (b.card.rating ?? 0) - (a.card.rating ?? 0);
      if (sort === 'rating') return (b.card.rating ?? 0) - (a.card.rating ?? 0) || (a.price ?? Infinity) - (b.price ?? Infinity);
      if (a.price === null || b.price === null) return (a.price === null ? 1 : 0) - (b.price === null ? 1 : 0) || a.card.name.localeCompare(b.card.name);
      return (sort === 'desc' ? b.price - a.price : a.price - b.price) || (b.card.rating ?? 0) - (a.card.rating ?? 0) || a.card.name.localeCompare(b.card.name);
    });
    $('resultCount').textContent = number(filtered.length) + (filtered.length === 1 ? ' result' : ' results') + ' · ' + (platform === 'pc' ? 'PC' : 'Console') + ' · coins';
    $('download').disabled = !filtered.length;
    freshness(); renderMore(true);
    const params = new URLSearchParams();
    if ($('search').value.trim()) params.set('q', $('search').value.trim());
    if (platform === 'pc') params.set('platform', 'pc');
    history.replaceState(null, '', location.pathname + (params.size ? '?' + params : ''));
    try { localStorage.setItem('ezz-market-platform', platform); } catch (_) { /* storage optional */ }
  }
  async function load(refresh = false) {
    if (busy) return;
    busy = true; $('refresh').disabled = true;
    try {
      const [data, roster, extra] = await Promise.all([window.EzzcoinsMarket.load(refresh), window.EzzcoinsMarket.fetchData('players.json'), window.EzzcoinsMarket.fetchData('market-cards.json')]);
      feed = data;
      cards = buildCards(roster, extra);
      cards.findCardIds = new Set(cards.filter(card => card.type !== 'unknown').map(card => card.id));
      applyFilters();
    } catch (error) {
      $('freshness').textContent = feed ? 'Refresh failed' : 'Prices unavailable';
      $('freshness').classList.add('stale');
      $('notice').textContent = feed ? 'The latest refresh failed. Displaying the previous feed from ' + date(feed.publishedAt[$('platform').value]) + '. Try Refresh again.' : 'The price feed could not be loaded. Try Refresh again.';
      $('notice').classList.add('error');
      if (!feed) { $('results').innerHTML = '<tr><td colspan="6" class="empty">Prices could not be loaded.</td></tr>'; $('resultCount').textContent = 'No price data loaded'; }
    } finally { busy = false; $('refresh').disabled = false; }
  }
  $('download').addEventListener('click', () => {
    const platform = $('platform').value;
    // Neutralize spreadsheet formulas in text supplied by upstream metadata.
    const csv = value => '"' + String(value ?? '').replace(/^[=+@-]/, "'$&").replace(/"/g, '""') + '"';
    const rows = [['EA item ID', 'Player', 'Rating', 'Version', 'Position', 'Club', 'Platform', 'Lowest Buy Now coins', 'Availability', 'Source', 'Feed published at'],
      ...filtered.map(({ card, price }) => [card.id, card.name, card.rating, card.version, card.position, card.club, platform, price, price === null ? stateLabel(card, platform) : 'Price available', feed.source, feed.publishedAt[platform]])];
    const blob = new Blob(['\uFEFF' + rows.map(row => row.map(csv).join(',')).join('\r\n')], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob), link = document.createElement('a');
    link.href = url; link.download = 'ezzcoins-fc27-' + platform + '-prices.csv'; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  let debounce;
  for (const id of filterIds) $(id).addEventListener(id === 'search' ? 'input' : 'change', () => {
    clearTimeout(debounce); debounce = setTimeout(applyFilters, id === 'search' ? 150 : 0);
  });
  $('more').addEventListener('click', () => renderMore());
  $('refresh').addEventListener('click', () => load(true));
  $('reset').addEventListener('click', () => {
    for (const id of ['search', 'type', 'minRating', 'maxPrice']) $(id).value = '';
    $('availability').value = 'priced'; $('sort').value = 'asc'; applyFilters();
  });
  const params = new URLSearchParams(location.search);
  let savedPlatform = 'console';
  try { savedPlatform = localStorage.getItem('ezz-market-platform') || 'console'; } catch (_) { /* storage optional */ }
  $('platform').value = (params.get('platform') || savedPlatform) === 'pc' ? 'pc' : 'console';
  $('search').value = params.get('q') || '';
  load();
  setInterval(() => { if (!document.hidden) load(true); }, 300000);
})();
