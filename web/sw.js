const CACHE_NAME = "visepanda-shell-v611-responsive-qa2";
const APP_SHELL = [
  "/",
  "/web/index.html",
  "/web/app.css",
  "/web/app.js",
  "/web/manifest.json",
  "/web/icon-192.png",
  "/web/icon-512.png",
  "/static/img/logo-panda.jpg",
  "/static/img/great-wall.jpg",
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (url.pathname.startsWith("/api/")) {
    event.respondWith(fetch(event.request));
    return;
  }
  event.respondWith(caches.match(event.request).then((cached) => cached || fetch(event.request)));
});
