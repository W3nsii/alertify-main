/* ALERTIFY service worker — offline access to emergency info */
var VERSION = 'alertify-v7';
var SHELL = [
  '/', '/contacts', '/guide', '/offline', '/about',
  '/static/css/style.css', '/static/js/app.js', '/static/js/contacts.js', '/static/img/logo.svg',
  '/static/vendor/leaflet-1.9.4/leaflet.css', '/static/vendor/leaflet-1.9.4/leaflet.js'
];
// Pages that are safe to keep for offline reading (no other users' data).
var CACHEABLE = [/^\/$/, /^\/contacts$/, /^\/guide(\/[a-z]+)?$/, /^\/about$/, /^\/offline$/,
  /^\/evacuation-centers$/, /^\/api\/centers$/, /^\/api\/contacts$/, /^\/report\/ALR-[A-F0-9]+$/, /^\/static\//];
var PRIVATE = /^\/report\//;

self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(VERSION).then(function (c) { return c.addAll(SHELL); }).then(function () { return self.skipWaiting(); }));
});

self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (k) { return k !== VERSION; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});

self.addEventListener('message', function (e) {
  if (e.data && e.data.type === 'clear-private') {
    caches.open(VERSION).then(function (c) {
      return c.keys().then(function (reqs) {
        return Promise.all(reqs.filter(function (r) { return PRIVATE.test(new URL(r.url).pathname); })
          .map(function (r) { return c.delete(r); }));
      });
    });
  }
});

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;
  var url = new URL(req.url);

  // Third-party libraries (Leaflet, Chart.js, fonts): stale-while-revalidate.
  if (url.origin !== location.origin) {
    if (/unpkg\.com|jsdelivr\.net|fonts\.(googleapis|gstatic)\.com/.test(url.host)) {
      e.respondWith(caches.open(VERSION).then(function (c) {
        return c.match(req).then(function (hit) {
          var net = fetch(req).then(function (res) { if (res.ok || res.type === 'opaque') c.put(req, res.clone()); return res; }).catch(function () { return hit; });
          return hit || net;
        });
      }));
    }
    return;
  }

  var cacheable = CACHEABLE.some(function (rx) { return rx.test(url.pathname); });
  // Network first, fall back to cache, then offline page.
  e.respondWith(fetch(req).then(function (res) {
    if (cacheable && res.ok) {
      var copy = res.clone();
      caches.open(VERSION).then(function (c) { c.put(req, copy); });
    }
    return res;
  }).catch(function () {
    return caches.match(req, { ignoreSearch: url.pathname === '/evacuation-centers' }).then(function (hit) {
      if (hit) return hit;
      if (req.mode === 'navigate') return caches.match('/offline');
      return new Response('', { status: 503 });
    });
  }));
});
