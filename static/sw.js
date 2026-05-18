const CACHE = 'love-pwa-v13';
const PRECACHE = [
  '/companion',
  '/static/style.css',
  '/static/app.js',
  '/static/manifest.json',
];

/* Install: pre-cache shell */
self.addEventListener('install', e => {
  self.skipWaiting();
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(PRECACHE).catch(() => {}))
  );
});

/* Activate: delete old caches */
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

/* Fetch: Network-first for API, Cache-first for assets */
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  // Always network for API calls and WebSocket upgrades
  if (url.pathname.startsWith('/chat') ||
      url.pathname.startsWith('/agi/') ||
      url.pathname.startsWith('/health')) {
    e.respondWith(fetch(e.request).catch(() => new Response('{"error":"offline"}', {
      headers: { 'Content-Type': 'application/json' }
    })));
    return;
  }

  // Cache-first for static assets
  e.respondWith(
    caches.match(e.request).then(cached => {
      if (cached) return cached;
      return fetch(e.request).then(resp => {
        if (resp.ok) {
          const clone = resp.clone();
          caches.open(CACHE).then(c => c.put(e.request, clone));
        }
        return resp;
      }).catch(() => caches.match('/companion'));
    })
  );
});

/* Background Sync: heartbeat while offline */
self.addEventListener('periodicsync', e => {
  if (e.tag === 'love-heartbeat') {
    e.waitUntil(fetch('/health').catch(() => {}));
  }
});
