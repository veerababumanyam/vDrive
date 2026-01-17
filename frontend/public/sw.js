// Service Worker for vDrive PWA
// Version 1.0.0

const CACHE_NAME = 'vdrive-cache-v1';
const RUNTIME_CACHE = 'vdrive-runtime-v1';

// Assets to cache on install
const PRECACHE_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/logo-light-192x192.png',
  '/logo-light-512x512.png',
  '/logo-dark-192x192.png',
  '/logo-dark-512x512.png'
];

// Install event - precache essential assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(PRECACHE_ASSETS))
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((name) => name !== CACHE_NAME && name !== RUNTIME_CACHE)
            .map((name) => caches.delete(name))
        );
      })
      .then(() => self.clients.claim())
  );
});

// Fetch event - network first, fallback to cache
self.addEventListener('fetch', (event) => {
  // Skip cross-origin requests
  if (!event.request.url.startsWith(self.location.origin)) {
    return;
  }

  // Handle API requests with network-first strategy
  if (event.request.url.includes('/api/')) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          // Clone response to cache it
          const responseClone = response.clone();
          caches.open(RUNTIME_CACHE).then((cache) => {
            cache.put(event.request, responseClone);
          });
          return response;
        })
        .catch(() => {
          // Fallback to cache if network fails
          return caches.match(event.request);
        })
    );
    return;
  }

  // Handle other requests with cache-first strategy
  event.respondWith(
    caches.match(event.request)
      .then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }

        return fetch(event.request)
          .then((response) => {
            // Don't cache non-successful responses
            if (!response || response.status !== 200 || response.type === 'error') {
              return response;
            }

            const responseClone = response.clone();
            caches.open(RUNTIME_CACHE).then((cache) => {
              cache.put(event.request, responseClone);
            });

            return response;
          });
      })
  );
});

// Handle messages from clients
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Background Sync event - process sync queue when online
self.addEventListener('sync', (event) => {
  if (event.tag === 'vdrive-sync') {
    event.waitUntil(
      processSyncQueue()
        .then(() => {
          console.log('Background sync completed successfully');
        })
        .catch((error) => {
          console.error('Background sync failed:', error);
          // Sync will be retried by the browser
          throw error;
        })
    );
  }
});

/**
 * Process sync queue - communicate with main thread to handle sync
 * Service Worker delegates sync processing to main app context
 */
async function processSyncQueue() {
  try {
    // Notify all clients that sync is starting
    const clients = await self.clients.matchAll({ includeUncontrolled: true, type: 'window' });

    if (clients.length === 0) {
      console.warn('No clients available to process sync');
      return;
    }

    // Send sync request to first available client
    // The client will handle the actual API calls using syncService
    const client = clients[0];
    client.postMessage({
      type: 'PROCESS_SYNC',
      timestamp: Date.now()
    });

    // Wait for client to respond
    // In a real implementation, you might use MessageChannel for request/response
    // For now, we trust the client will process the sync
    return Promise.resolve();
  } catch (error) {
    console.error('Failed to process sync queue:', error);
    throw error;
  }
}
