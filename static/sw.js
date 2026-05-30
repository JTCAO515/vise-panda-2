// VisePanda Service Worker v2 — install-time + runtime cache
const CACHE = 'vp-v6';
const RUNTIME = 'vp-runtime';

const PRECACHE = [
  '/',
  '/chat',
  '/trips',
  '/sw.js',
  '/static/landing.js',
  '/static/chat.js',
  '/static/trips.js',
  '/static/auth.js',
  '/static/profile.js',
  '/static/i18n.js',
  '/static/pwa.js',
  '/static/manifest.json',
  '/static/img/logo-32.png',
  '/static/img/logo-64.png',
  '/static/img/logo-192.png',
  '/static/img/logo-512.png',
  '/static/img/favicon.ico',
  '/static/img/og-image.png',
];

function fetchWithTimeout(req, ms) {
  return new Promise((resolve, reject) => {
    const id = setTimeout(() => reject(new Error('timeout')), ms);
    fetch(req).then(r => { clearTimeout(id); resolve(r); }).catch(err => { clearTimeout(id); reject(err); });
  });
}

// Install: warm cache with critical static assets (don't fail on missing)
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(cache =>
      Promise.allSettled(PRECACHE.map(url =>
        fetch(url).then(resp => { if (resp.ok) cache.put(url, resp); })
      ))
    ).then(() => self.skipWaiting())
  );
});

// Activate: reclaim all clients, clean old caches
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.map(k => {
        if (k !== CACHE && k !== RUNTIME) return caches.delete(k);
      }))
    ).then(() => self.clients.claim())
  );
});

// Fetch strategy
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  const { pathname } = url;

  // API calls — network only, no cache
  if (pathname.startsWith('/api/')) return;

  // Navigations — network-first with short timeout, fallback to cache
  if (e.request.mode === 'navigate') {
    e.respondWith(
      caches.match(e.request).then(cached => {
        const fetchPromise = fetchWithTimeout(e.request, 3000).then(resp => {
          if (resp && resp.ok) {
            const clone = resp.clone();
            caches.open(CACHE).then(cache => cache.put(e.request, clone));
          }
          return resp;
        }).catch(() => cached);
        return fetchPromise || cached;
      })
    );
    return;
  }

  // CDN fonts / supabase — cache-first with background refresh
  if (url.hostname.includes('cdnfonts') || url.hostname.includes('esm.sh') || url.hostname.includes('vercel')) {
    e.respondWith(
      caches.match(e.request).then(cached => {
        const fetchPromise = fetch(e.request).then(resp => {
          if (resp.ok) {
            const clone = resp.clone();
            caches.open(RUNTIME).then(cache => cache.put(e.request, clone));
          }
          return resp;
        }).catch(() => cached);
        return cached || fetchPromise;
      })
    );
    return;
  }

  // Static assets (JS, CSS, SVG inside our domain) — cache-first
  if (pathname.startsWith('/static/') || pathname === '/favicon.ico' || pathname === '/favicon.png') {
    e.respondWith(
      caches.match(e.request).then(cached => {
        const fetched = fetch(e.request).then(resp => {
          if (resp.ok) {
            const clone = resp.clone();
            caches.open(CACHE).then(cache => cache.put(e.request, clone));
          }
          return resp;
        });
        return cached || fetched;
      })
    );
    return;
  }

  // Other requests — default to cache-first fallback
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request))
  );
});
