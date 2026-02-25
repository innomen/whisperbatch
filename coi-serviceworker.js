/*
 * Minimal Cross-Origin Isolation service worker.
 * Injects COOP/COEP headers so SharedArrayBuffer is available,
 * which enables multi-threaded WASM (ONNX Runtime uses this).
 * Works on GitHub Pages and any static server.
 */

self.addEventListener('install', () => self.skipWaiting());

self.addEventListener('activate', (e) => {
  e.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (e) => {
  if (e.request.cache === 'only-if-cached' && e.request.mode !== 'same-origin') return;

  e.respondWith(
    fetch(e.request).then((response) => {
      if (response.status === 0) return response;

      const headers = new Headers(response.headers);
      headers.set('Cross-Origin-Embedder-Policy', 'credentialless');
      headers.set('Cross-Origin-Opener-Policy', 'same-origin');

      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers,
      });
    }).catch((err) => {
      console.error('[COI-SW] Fetch failed:', err);
      return new Response('Service worker fetch failed', { status: 502 });
    })
  );
});
