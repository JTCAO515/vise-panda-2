// VisePanda PWA bootstrap
// Registers the Service Worker (served at /sw.js) for offline caching.
(function () {
  if (!('serviceWorker' in navigator)) return;
  window.addEventListener('load', function () {
    navigator.serviceWorker.register('/sw.js', { scope: '/' }).catch(function () {
      // Silent fail: PWA is optional
    });
  });
})();

