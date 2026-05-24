// Register PWA service worker
if('serviceWorker' in navigator){
    navigator.serviceWorker.register('/static/sw.js');
}
