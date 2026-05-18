const CACHE_NAME = 'love-hud-v1';
const ASSETS = [
  '/companion',
  '/static/style.css',
  '/static/app.js',
  '/static/manifest.json',
  'https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700;900&family=Rajdhani:wght@300;400;500;600;700&display=swap'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS))
  );
});

self.addEventListener('fetch', event => {
  // Always try network first to get the latest updates
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
