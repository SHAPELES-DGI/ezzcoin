/* © 2026 Ezzcoins. Card pictures from ezzcoins.com.
   The server keeps a copy of every FC 27 card picture the site uses in card-img/ (scripts/server/ezzcoins-cards-sync).
   local(url) turns a FUT.GG card picture address into that copy's address. If the copy can't load (a brand-new
   card not copied yet, or the GitHub Pages backup, which has no card-img/), the picture falls back to FUT.GG. */
(() => {
  'use strict';
  if (window.EzzCardImg) return;
  const root = new URL('./', document.currentScript.src);
  const CARD = /^https:\/\/game-assets\.fut\.gg\/.*\/futgg-player-item-card\/(27-\d+\.[0-9a-f]+\.webp)$/;
  const remote = new Map();
  function local(url) {
    const match = CARD.exec(String(url || ''));
    if (!match) return url || '';
    const own = new URL('card-img/' + match[1], root).href;
    remote.set(own, url);
    return own;
  }
  // One listener for every card picture drawn by the page's scripts. Pictures written into the page itself carry
  // their own onerror (they also switch to the designed card if FUT.GG fails too), so they are left alone here.
  document.addEventListener('error', event => {
    const img = event.target;
    if (!(img instanceof HTMLImageElement) || img.hasAttribute('onerror') || img.dataset.triedRemote) return;
    const fallback = remote.get(img.currentSrc || img.src) || remote.get(img.src);
    if (!fallback) return;
    img.dataset.triedRemote = '1';
    event.stopImmediatePropagation();
    img.src = fallback;
  }, true);
  window.EzzCardImg = { local };
})();
