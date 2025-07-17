// Mental Health Agent - Service Worker
// Provides offline support, caching, and push notifications

const CACHE_NAME = 'mental-health-agent-v1.0.0';
const OFFLINE_URL = '/offline.html';
const EMERGENCY_URL = '/emergency';

// Resources to cache for offline use
const STATIC_CACHE_URLS = [
  '/',
  '/chat',
  '/emergency',
  '/resources',
  '/offline.html',
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png',
  // Add critical CSS and JS files
  '/static/css/main.css',
  '/static/js/main.js'
];

// Emergency resources that must be available offline
const EMERGENCY_CACHE_URLS = [
  '/emergency',
  '/api/agent/emergency-resources',
  '/crisis-resources.json'
];

// Install event - cache static resources
self.addEventListener('install', event => {
  console.log('Service Worker installing...');
  
  event.waitUntil(
    Promise.all([
      // Cache static resources
      caches.open(CACHE_NAME).then(cache => {
        console.log('Caching static resources');
        return cache.addAll(STATIC_CACHE_URLS);
      }),
      
      // Cache emergency resources
      caches.open(`${CACHE_NAME}-emergency`).then(cache => {
        console.log('Caching emergency resources');
        return cache.addAll(EMERGENCY_CACHE_URLS);
      })
    ]).then(() => {
      console.log('Service Worker installed successfully');
      // Skip waiting to activate immediately
      return self.skipWaiting();
    })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('Service Worker activating...');
  
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME && 
              cacheName !== `${CACHE_NAME}-emergency` &&
              cacheName.startsWith('mental-health-agent-')) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('Service Worker activated');
      // Take control of all clients immediately
      return self.clients.claim();
    })
  );
});

// Fetch event - handle network requests with caching strategy
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Handle different types of requests
  if (url.pathname.startsWith('/api/')) {
    // API requests - network first with cache fallback
    event.respondWith(handleApiRequest(request));
  } else if (url.pathname === '/emergency' || url.pathname.startsWith('/crisis')) {
    // Emergency pages - cache first for immediate access
    event.respondWith(handleEmergencyRequest(request));
  } else if (STATIC_CACHE_URLS.includes(url.pathname)) {
    // Static resources - cache first
    event.respondWith(handleStaticRequest(request));
  } else {
    // Other requests - network first with offline fallback
    event.respondWith(handleGeneralRequest(request));
  }
});

// Handle API requests - network first with cache fallback
async function handleApiRequest(request) {
  const url = new URL(request.url);
  
  try {
    // Try network first
    const networkResponse = await fetch(request);
    
    // Cache successful responses (except POST/PUT/DELETE)
    if (networkResponse.ok && request.method === 'GET') {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.log('Network failed for API request, trying cache:', url.pathname);
    
    // Try cache fallback
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Special handling for emergency API
    if (url.pathname.includes('emergency')) {
      return new Response(JSON.stringify({
        emergency_resources: [
          {
            name: "National Suicide Prevention Lifeline",
            phone: "988",
            description: "24/7 crisis support"
          },
          {
            name: "Crisis Text Line",
            phone: "741741",
            description: "Text HOME for crisis support"
          },
          {
            name: "Emergency Services",
            phone: "911",
            description: "Immediate emergency assistance"
          }
        ]
      }), {
        headers: { 'Content-Type': 'application/json' },
        status: 200
      });
    }
    
    // Return offline response for other API calls
    return new Response(JSON.stringify({
      error: "Offline",
      message: "This feature requires an internet connection"
    }), {
      headers: { 'Content-Type': 'application/json' },
      status: 503
    });
  }
}

// Handle emergency requests - cache first for immediate access
async function handleEmergencyRequest(request) {
  try {
    // Try cache first for immediate access
    const cachedResponse = await caches.match(request, {
      cacheName: `${CACHE_NAME}-emergency`
    });
    
    if (cachedResponse) {
      // Update cache in background
      fetch(request).then(response => {
        if (response.ok) {
          caches.open(`${CACHE_NAME}-emergency`).then(cache => {
            cache.put(request, response.clone());
          });
        }
      }).catch(() => {
        // Ignore network errors for background updates
      });
      
      return cachedResponse;
    }
    
    // If not in cache, try network
    const networkResponse = await fetch(request);
    
    // Cache the response
    if (networkResponse.ok) {
      const cache = await caches.open(`${CACHE_NAME}-emergency`);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.log('Emergency request failed, serving offline emergency page');
    
    // Serve offline emergency page
    return new Response(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Emergency Resources - Mental Health Agent</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
          body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
          .emergency { background: #dc2626; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
          .resource { background: white; padding: 15px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
          .phone { font-size: 24px; font-weight: bold; color: #dc2626; }
          .offline-notice { background: #f59e0b; color: white; padding: 10px; border-radius: 4px; margin-bottom: 20px; }
        </style>
      </head>
      <body>
        <div class="offline-notice">
          You are currently offline. These emergency resources are always available.
        </div>
        
        <div class="emergency">
          <h1>🚨 Emergency Resources</h1>
          <p>If you are in immediate danger, call 911 now.</p>
        </div>
        
        <div class="resource">
          <h2>National Suicide Prevention Lifeline</h2>
          <div class="phone">988</div>
          <p>24/7 crisis support and suicide prevention</p>
        </div>
        
        <div class="resource">
          <h2>Crisis Text Line</h2>
          <div class="phone">Text HOME to 741741</div>
          <p>24/7 crisis support via text message</p>
        </div>
        
        <div class="resource">
          <h2>Emergency Services</h2>
          <div class="phone">911</div>
          <p>Immediate emergency assistance</p>
        </div>
        
        <div class="resource">
          <h2>SAMHSA National Helpline</h2>
          <div class="phone">1-800-662-4357</div>
          <p>Treatment referral and information service</p>
        </div>
      </body>
      </html>
    `, {
      headers: { 'Content-Type': 'text/html' },
      status: 200
    });
  }
}

// Handle static requests - cache first
async function handleStaticRequest(request) {
  try {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      return caches.match(OFFLINE_URL);
    }
    
    throw error;
  }
}

// Handle general requests - network first with offline fallback
async function handleGeneralRequest(request) {
  try {
    const networkResponse = await fetch(request);
    
    // Cache successful responses
    if (networkResponse.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      return caches.match(OFFLINE_URL);
    }
    
    throw error;
  }
}

// Push notification event
self.addEventListener('push', event => {
  console.log('Push notification received');
  
  const options = {
    body: 'You have a new message from your Mental Health Agent',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
    vibrate: [200, 100, 200],
    data: {
      url: '/chat'
    },
    actions: [
      {
        action: 'open',
        title: 'Open Chat',
        icon: '/icons/chat-96x96.png'
      },
      {
        action: 'emergency',
        title: 'Emergency Help',
        icon: '/icons/emergency-96x96.png'
      }
    ],
    requireInteraction: false,
    silent: false
  };
  
  if (event.data) {
    try {
      const data = event.data.json();
      
      // Handle crisis notifications with high priority
      if (data.type === 'crisis') {
        options.body = data.message || 'Crisis support resources are available';
        options.requireInteraction = true;
        options.vibrate = [300, 100, 300, 100, 300];
        options.tag = 'crisis';
        options.renotify = true;
        options.actions = [
          {
            action: 'emergency',
            title: 'Get Help Now',
            icon: '/icons/emergency-96x96.png'
          },
          {
            action: 'dismiss',
            title: 'Dismiss',
            icon: '/icons/dismiss-96x96.png'
          }
        ];
      } else {
        options.body = data.message || options.body;
        options.tag = data.tag || 'general';
      }
    } catch (e) {
      console.error('Error parsing push data:', e);
    }
  }
  
  event.waitUntil(
    self.registration.showNotification('Mental Health Agent', options)
  );
});

// Notification click event
self.addEventListener('notificationclick', event => {
  console.log('Notification clicked:', event.action);
  
  event.notification.close();
  
  let url = '/';
  
  switch (event.action) {
    case 'open':
      url = '/chat';
      break;
    case 'emergency':
      url = '/emergency';
      break;
    case 'dismiss':
      return; // Just close the notification
    default:
      url = event.notification.data?.url || '/';
  }
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(clientList => {
      // Check if there's already a window open
      for (const client of clientList) {
        if (client.url.includes(url) && 'focus' in client) {
          return client.focus();
        }
      }
      
      // Open new window
      if (clients.openWindow) {
        return clients.openWindow(url);
      }
    })
  );
});

// Background sync event
self.addEventListener('sync', event => {
  console.log('Background sync triggered:', event.tag);
  
  if (event.tag === 'sync-messages') {
    event.waitUntil(syncMessages());
  } else if (event.tag === 'sync-feedback') {
    event.waitUntil(syncFeedback());
  }
});

// Sync pending messages when back online
async function syncMessages() {
  try {
    // Get pending messages from IndexedDB
    const pendingMessages = await getPendingMessages();
    
    for (const message of pendingMessages) {
      try {
        const response = await fetch('/api/agent/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${message.token}`
          },
          body: JSON.stringify(message.data)
        });
        
        if (response.ok) {
          // Remove from pending messages
          await removePendingMessage(message.id);
          
          // Notify user of successful sync
          await self.registration.showNotification('Messages Synced', {
            body: 'Your offline messages have been sent',
            icon: '/icons/icon-192x192.png',
            tag: 'sync-success'
          });
        }
      } catch (error) {
        console.error('Failed to sync message:', error);
      }
    }
  } catch (error) {
    console.error('Background sync failed:', error);
  }
}

// Sync pending feedback when back online
async function syncFeedback() {
  try {
    // Implementation for syncing feedback data
    console.log('Syncing feedback data...');
  } catch (error) {
    console.error('Feedback sync failed:', error);
  }
}

// Helper functions for IndexedDB operations
async function getPendingMessages() {
  // Implementation would use IndexedDB to get pending messages
  return [];
}

async function removePendingMessage(id) {
  // Implementation would remove message from IndexedDB
  console.log('Removing pending message:', id);
}

// Message event for communication with main thread
self.addEventListener('message', event => {
  console.log('Service Worker received message:', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

console.log('Mental Health Agent Service Worker loaded');
