/* © 2026 Ezzcoins. All rights reserved. */
// Pages: always from the network, with the last copy as an offline fallback. Live data (data/*.json): never cached here.
// Flags, fonts and icons: from the cache once loaded.
const V = "ezz-1";
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (e) => e.waitUntil((async () => {
  for (const k of await caches.keys()) if (k !== V) await caches.delete(k);
  await self.clients.claim();
})()));
const keep = (req, res) => { if (res && res.ok) { const c = res.clone(); caches.open(V).then((ca) => ca.put(req, c)); } return res; };
self.addEventListener("fetch", (e) => {
  const r = e.request, u = new URL(r.url);
  if (r.method !== "GET" || u.origin !== location.origin || u.pathname.includes("/data/")) return;
  if (r.mode === "navigate") {
    e.respondWith(fetch(r).then((res) => keep(r, res)).catch(async () => (await caches.match(r)) || (await caches.match(new URL("./", location).href)) || Response.error()));
    return;
  }
  if (/\/(flags\/|fonts\/|icon-|favicon|apple-touch-icon|mark\.svg)/.test(u.pathname)) {
    e.respondWith(caches.match(r).then((m) => m || fetch(r).then((res) => keep(r, res))));
  }
});
