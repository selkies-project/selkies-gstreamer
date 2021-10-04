/**
 * Copyright 2021 The Selkies Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

const cacheVersion = "CACHE_VERSION";
var cacheName = 'PWA_CACHE';
var filesToCache = [
  'index.html?ts=CACHE_VERSION',
  'icon-192x192.png?ts=CACHE_VERSION',
  'icon-512x512.png?ts=CACHE_VERSION',
  /* cache assets from app launcher */
  'app.js?ts=CACHE_VERSION',
  'input.js?ts=CACHE_VERSION',
  'signalling.js?ts=CACHE_VERSION',
  'webrtc.js?ts=CACHE_VERSION'
];

function getCacheName() {
  return cacheName + "_" + cacheVersion;
}

function deleteCache() {
  caches.keys().then(cacheNames => {
    return Promise.all(
      cacheNames.map(name => {
        if (name.startsWith(cacheName) && name !== getCacheName()) {
          return caches.delete(name);
        }
      })
    );
  });
}

// on activation we clean up the previously registered service workers
self.addEventListener('activate', evt => {
  evt.waitUntil(deleteCache());
});

/* Start the service worker and cache all of the app's content */
self.addEventListener('install', function(e) {
  e.waitUntil(
    caches.open(getCacheName()).then(function(cache) {
      return cache.addAll(filesToCache);
    })
  );
});

/* Serve cached content when offline */
self.addEventListener('fetch', function(e) {
  const clientId = e.clientId || e.resultingClientId;
  e.respondWith(
    caches.match(e.request)
      .then(function(response) {
        return response || fetch(e.request, {
          credentials: 'include',
          redirect: 'manual',
          mode: 'no-cors',
        })
      })
      .then( (response) => {
        if (response.type === "opaqueredirect" && !e.request.url.match("favicon")) {
          console.log("saw opaqueredirect response when fetching " + e.request.url + ", deleting cache and sending reload to client: " + e.clientId);

          // Notify client that network is offline.
          if (clientId) {
            clients.get(clientId).then((client) => {
              var msg = {
                msg: "reload",
              };
              console.log("sending message to client: " + client.id, msg);
              client.postMessage(msg);
            });
          }
          deleteCache();
        }
        return response;
      })
      .catch(function(err) {
        // Attempt to fetch non-cached resource failed.
        // Hack to make this PWA installable, always return valid Response object.
        return new Response();
      })
    );
});
