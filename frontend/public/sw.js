// WiFiSense Local — Service Worker (PWA)
// Estratégia: Cache First para assets estáticos, Network First para API

const CACHE_NAME = "wifisense-v1";
const STATIC_ASSETS = [
  "/",
  "/index.html",
  "/manifest.json",
];

// ── Instalação ────────────────────────────────────────────────────────────────
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

// ── Ativação — remove caches antigos ─────────────────────────────────────────
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// ── Fetch — estratégia mista ──────────────────────────────────────────────────
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // API requests: Network First (sem cache)
  if (url.pathname.startsWith("/api/") || url.pathname.startsWith("/ws")) {
    event.respondWith(fetch(request).catch(() => new Response("Offline", { status: 503 })));
    return;
  }

  // Assets estáticos: Cache First
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request).then((response) => {
        if (!response || response.status !== 200 || response.type !== "basic") return response;
        const clone = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
        return response;
      });
    })
  );
});

// ── Notificações Push ─────────────────────────────────────────────────────────
self.addEventListener("push", (event) => {
  if (!event.data) return;
  let data;
  try { data = event.data.json(); } catch { data = { title: "WiFiSense", body: event.data.text() }; }

  const options = {
    body: data.body ?? "Novo alerta do WiFiSense",
    icon: "/icons/icon-192x192.png",
    badge: "/icons/icon-192x192.png",
    tag: data.tag ?? "wifisense-alert",
    renotify: true,
    requireInteraction: data.requireInteraction ?? false,
    data: { url: data.url ?? "/" },
    actions: [
      { action: "open", title: "Ver Painel" },
      { action: "dismiss", title: "Dispensar" },
    ],
  };

  event.waitUntil(self.registration.showNotification(data.title ?? "WiFiSense", options));
});

// ── Clique na notificação ─────────────────────────────────────────────────────
self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  if (event.action === "dismiss") return;

  const targetUrl = event.notification.data?.url ?? "/";
  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then((windowClients) => {
      const existing = windowClients.find((c) => c.url === targetUrl && "focus" in c);
      if (existing) return existing.focus();
      return clients.openWindow(targetUrl);
    })
  );
});
