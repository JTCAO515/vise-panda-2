// VisePanda Service Worker — PWA offline support
const CACHE = 'vp-v1';
const STATIC = [
    '/',
    '/chat',
    '/trips',
    '/static/landing.js',
    '/static/chat.js',
    '/static/trips.js',
    '/static/auth.js',
    '/static/i18n.js',
    '/static/manifest.json',
    '/static/icon.svg',
];

// Install: cache all static assets
self.addEventListener('install', e => {
    e.waitUntil(
        caches.open(CACHE).then(cache => cache.addAll(STATIC))
    );
    self.skipWaiting();
});

// Activate: clean old caches
self.addEventListener('activate', e => {
    e.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
        )
    );
    self.clients.claim();
});

// Fetch: cache-first for static, network-first for API
self.addEventListener('fetch', e => {
    const url = new URL(e.request.url);

    // API calls: network first, no cache
    if (url.pathname.startsWith('/api/')) {
        return; // Let browser handle — don't cache API
    }

    // Static assets: cache first, network fallback
    e.respondWith(
        caches.match(e.request).then(cached => {
            const fetched = fetch(e.request).then(resp => {
                if (resp.ok) {
                    const clone = resp.clone();
                    caches.open(CACHE).then(cache => cache.put(e.request, clone));
                }
                return resp;
            }).catch(() => cached);

            return cached || fetched;
        })
    );
});
