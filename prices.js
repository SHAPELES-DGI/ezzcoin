(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const number = value => value.toLocaleString('en-US');
  const escape = value => String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
  const normalize = window.EzzcoinsSite.normalize;
  let feed = null, cards = [], filtered = [], shown = 0, busy = false, dayAgo = null, catalogue = null, agoChecked = 0, quoteError = false;
  // 24h change: today's price against the recorded price from about a day ago (data/day-ago.json).
  const MOVER_MIN = 1000; // mover sorts skip cards under this many coins, where one listing swings the percentage
  const change = (id, price, platform) => {
    const ref = dayAgo?.get(id)?.[platform === 'pc' ? 1 : 0];
    return price !== null && ref ? { pct: (price / ref - 1) * 100, ref } : null;
  };
  const changeText = c => c ? (Math.abs(c.pct) < 0.05 ? '0.0%' : (c.pct > 0 ? '▲ +' : '▼ ') + c.pct.toFixed(1) + '%') : '';
  const filterIds = ['search', 'platform', 'type', 'minRating', 'maxPrice', 'availability', 'sort'];
  const date = value => new Date(value).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZoneName: 'short' });
  const stateLabel = (card, platform) => {
    const quote = window.EzzcoinsMarket.lookup(feed, card.id, platform);
    if (!quote) return 'Not in market feed';
    if (quote.status === 0) return 'No listing recorded';
    return feed.statusLabels?.[String(quote.status)] || 'No market price';
  };
  function freshness() {
    if (!feed) return;
    const platform = $('platform').value;
    const time = feed.publishedAt[platform];
    const age = window.EzzcoinsMarket.freshness(time), minutes = age.ageMinutes;
    const delayed = age.freshness !== 'fresh';
    $('freshness').textContent = age.freshness === 'fresh' ? 'Current price feed' : age.freshness === 'delayed' ? 'Delayed prices' : 'Outdated prices';
    $('freshness').classList.toggle('stale', delayed);
    const futbin = (feed.primaryCoverage && feed.primaryCoverage[platform]) || 0;
    $('sourceTime').textContent = (futbin > 0 ? 'FUTBIN for ' + number(futbin) + ' cards, FUT.GG for the rest' : 'Source: FUT.GG') + ' · feed: ' + date(time);
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
      const quote=window.EzzcoinsMarket.lookup(feed,card.id,platform),src=quote?.src||feed.source;
      const name=card.url?`<a href="${escape(card.url)}"${card.url.startsWith('https:')?' target="_blank" rel="noopener"':''}>${escape(card.name)}</a>`:escape(card.name);
      const graph=quote?`<button class="graph-button" data-price-graph="${quote.id}" data-player-name="${escape(card.name+' · '+card.version)}" data-price-platform="${platform}" aria-label="Price history for ${escape(card.name+' '+card.version)}">Graph</button>`:'';
      const color = card.rating < 65 ? ' bronze' : card.rating < 75 ? ' silver' : '';
      const c = filtered.changes.get(card.id), dir = !c ? '' : c.pct >= 0.05 ? ' up' : c.pct <= -0.05 ? ' down' : ' flat';
      const chg = c ? `<small class="chg${dir}" title="${escape('About 24 hours ago: ' + number(c.ref) + ' coins')}">${changeText(c)} <span>24h</span></small>` : '';
      return `<tr><td class="player"><strong>${name}</strong><small>${escape(card.version)} · ID ${card.id}</small></td><td>${card.rating ? `<span class="rating${color}">${card.rating}</span>` : '—'}</td><td>${escape(card.position || '—')}</td><td class="club">${escape(card.club || card.nation || '—')}</td><td class="price${price === null ? ' unavailable' : ''}">${price === null ? escape(stateLabel(card, platform)) : number(price) + chg + (quote?.freshness!=='fresh'?`<small class="quote-age">${quote?.freshness==='delayed'?'Delayed quote':'Outdated quote'}</small>`:'')}</td><td><span class="source" title="${escape((quote?.freshness||'Unknown age')+' · '+date(quote?.at||feed.publishedAt[platform]))}">${escape(src)}</span>${graph}</td></tr>`;
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
    filtered = cards.map(card => { const quote = window.EzzcoinsMarket.lookup(feed, card.id, platform), price = quote?.price ?? null;
      return { card, price, chg: quote ? change(quote.id, price, platform) : null }; }).filter(({ card, price }) =>
      terms.every(term => card.key.includes(term)) && (!type || card.type === type) && (card.rating ?? 0) >= minRating &&
      (budget === null || price !== null && price <= budget) && (availability === 'all' || (availability === 'priced' ? price !== null : price === null)));
    const sort = $('sort').value;
    filtered.changes = new Map(filtered.filter(x => x.chg).map(x => [x.card.id, x.chg]));
    const mover = x => x.chg && x.price >= MOVER_MIN && x.chg.ref >= MOVER_MIN ? x.chg.pct : null;
    filtered.sort((a, b) => {
      if (sort === 'rise' || sort === 'fall') {
        const ma = mover(a), mb = mover(b);
        if (ma === null || mb === null) return (ma === null) - (mb === null) || (a.price ?? Infinity) - (b.price ?? Infinity);
        return sort === 'rise' ? mb - ma : ma - mb;
      }
      if (sort === 'name') return a.card.name.localeCompare(b.card.name) || (b.card.rating ?? 0) - (a.card.rating ?? 0);
      if (sort === 'rating') return (b.card.rating ?? 0) - (a.card.rating ?? 0) || (a.price ?? Infinity) - (b.price ?? Infinity);
      if (a.price === null || b.price === null) return (a.price === null ? 1 : 0) - (b.price === null ? 1 : 0) || a.card.name.localeCompare(b.card.name);
      return (sort === 'desc' ? b.price - a.price : a.price - b.price) || (b.card.rating ?? 0) - (a.card.rating ?? 0) || a.card.name.localeCompare(b.card.name);
    });
    $('resultCount').textContent = number(filtered.length) + (filtered.length === 1 ? ' result' : ' results') + ' · ' + (platform === 'pc' ? 'PC' : 'Console') + ' · coins'
      + (sort === 'rise' || sort === 'fall' ? (dayAgo ? ' · 24h change, cards worth ' + number(MOVER_MIN) + '+ first' : ' · 24h change not available yet') : '');
    $('download').disabled = !filtered.length;
    freshness(); renderMore(true);
    const params = new URLSearchParams();
    const defaults = {search:'',platform:'console',type:'',minRating:'',maxPrice:'',availability:'priced',sort:'asc'};
    for (const id of filterIds) { const value=$(id).value.trim(); if(value!==defaults[id])params.set(id==='search'?'q':id,value); }
    history.replaceState(null, '', location.pathname + (params.size ? '?' + params : ''));
    try { localStorage.setItem('ezz-market-platform', platform); } catch (_) { /* storage optional */ }
  }
  async function load(refresh = false) {
    if (busy) return;
    busy = true; quoteError = false; $('refresh').disabled = true;
    try {
      const M=window.EzzcoinsMarket;
      const catalogueRequest=catalogue?Promise.resolve(catalogue):Promise.all([
        M.fetchData('players.json'),M.fetchData('market-cards.json'),
        M.fetchData('newcards.json').catch(()=>({cards:[]})),M.fetchData('legends.json').catch(()=>({cards:[]})),M.fetchData('card-ids.json').catch(()=>({}))
      ]);
      const agoRequest=Date.now()-agoChecked<3600000?Promise.resolve(null):M.fetchData('day-ago.json').catch(()=>null);
      const [data,meta,ago]=await Promise.all([M.load(refresh),catalogueRequest,agoRequest]);
      if(ago){agoChecked=Date.now();dayAgo=null;}
      if (ago && Array.isArray(ago.rows) && ago.cols?.join(',') === 'id,console,pc' && Date.now() - Date.parse(ago.updatedAt) < 6 * 3600000)
        dayAgo = new Map(ago.rows.filter(r => Array.isArray(r) && r.length === 3).map(r => [r[0], [r[1], r[2]]]));
      feed=data;catalogue=meta;
      cards=window.EzzcoinsPrices.buildCards(meta[0],meta[1],feed,M.lookup,[...(meta[2].cards||[]),...(meta[3].cards||[])],meta[4]);
      cards.findCardIds=new Set(cards.filter(card=>card.type!=='unknown').map(card=>card.id));
      applyFilters();
      if(quoteError){$('notice').textContent='The latest price check failed. Previous quotes remain visible with their source times. Try Refresh again.';$('notice').classList.add('error');}
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
    const rows = [['EA item ID', 'Player', 'Rating', 'Version', 'Position', 'Club', 'Platform', 'Lowest Buy Now coins', '24h change %', 'Availability', 'Source', 'Feed published at'],
      ...filtered.map(({ card, price, chg }) => [card.id, card.name, card.rating, card.version, card.position, card.club, platform, price, chg ? chg.pct.toFixed(1) : '', price === null ? stateLabel(card, platform) : 'Price available', window.EzzcoinsMarket.lookup(feed,card.id,platform)?.src||feed.source, window.EzzcoinsMarket.lookup(feed,card.id,platform)?.at||feed.publishedAt[platform]])];
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
  $('refresh').addEventListener('click', () => { catalogue=null;agoChecked=0;load(true); });
  $('reset').addEventListener('click', () => {
    for (const id of ['search', 'type', 'minRating', 'maxPrice']) $(id).value = '';
    $('availability').value = 'priced'; $('sort').value = 'asc'; applyFilters();
  });
  const params = new URLSearchParams(location.search);
  let savedPlatform = 'console';
  try { savedPlatform = localStorage.getItem('ezz-market-platform') || 'console'; } catch (_) { /* storage optional */ }
  $('platform').value = (params.get('platform') || savedPlatform) === 'pc' ? 'pc' : 'console';
  $('search').value = params.get('q') || '';
  for(const id of ['type','availability','sort']){const value=params.get(id);if(value!==null&&[...$(id).options].some(o=>o.value===value))$(id).value=value;}
  for(const id of ['minRating','maxPrice']){const value=params.get(id);if(value!==null&&value!==''&&Number.isFinite(+value)&&+value>=0&&+value<=(id==='minRating'?99:15000000))$(id).value=value;}
  load();
  window.addEventListener('ezzcoins:quotes',event=>{quoteError=false;if(busy||!catalogue)return;feed=event.detail;cards=window.EzzcoinsPrices.buildCards(catalogue[0],catalogue[1],feed,window.EzzcoinsMarket.lookup,[...(catalogue[2].cards||[]),...(catalogue[3].cards||[])],catalogue[4]);cards.findCardIds=new Set(cards.filter(c=>c.type!=='unknown').map(c=>c.id));applyFilters();});
  window.addEventListener('ezzcoins:quote-error',()=>{quoteError=true;if(feed){freshness();$('notice').textContent='The last price check failed. Previous quotes remain visible with their source times. Try Refresh again.';}});
  setInterval(()=>{if(!document.hidden&&Date.now()-agoChecked>=3600000)load();},60000);
})();


