self.addEventListener('install', function(e) {
  self.skipWaiting();
});

self.addEventListener('activate', function(e) {
  e.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          return caches.delete(cacheName);
        })
      );
    }).then(function() {
      self.clients.claim();
      // Force unregister
      self.registration.unregister();
    })
  );
});

self.addEventListener('fetch', function(e) {
  // Bypass all caching and fetch from network
  e.respondWith(fetch(e.request));
});