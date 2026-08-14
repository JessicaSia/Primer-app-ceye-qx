const CACHE_NAME = 'ceye-qx-pwa-v2';
const APP_SHELL = [
  '/',
  '/manifest.webmanifest',
  '/icons/surgical-icon.svg',
  '/icons/surgical-icon-192.png',
  '/icons/surgical-icon-512.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) =>
      Promise.all(
        cacheNames
          .filter((cacheName) => cacheName !== CACHE_NAME)
          .map((cacheName) => caches.delete(cacheName))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);

  if (request.method !== 'GET') return;
  if (url.pathname.startsWith('/api/') || url.hostname.includes('onrender.com')) return;

  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const responseCopy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put('/', responseCopy));
          return response;
        })
        .catch(() => caches.match('/'))
    );
    return;
  }

  if (url.origin === self.location.origin) {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        const networkResponse = fetch(request)
          .then((response) => {
            if (response.ok) {
              const responseCopy = response.clone();
              caches.open(CACHE_NAME).then((cache) => cache.put(request, responseCopy));
            }
            return response;
          })
          .catch(() => cachedResponse);

        return cachedResponse || networkResponse;
      })
    );
  }
});
