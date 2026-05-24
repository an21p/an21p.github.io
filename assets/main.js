// ---- Card visibility trigger (sticker + tag animations) ----
(function initCardObserver() {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.2 }
  );
  document.querySelectorAll(".card").forEach((card) => observer.observe(card));
})();

window.CONFIG = {
  QUEENS_AZURE_API_KEY: "__QUEENS_AZURE_API_KEY__",
  VOL_AZURE_API_KEY: "__VOL_AZURE_API_KEY__"
};

// Track last created object URL so we can revoke it when replaced
let _lastResultObjectUrl = null;

// ---- HUD clock (UTC, HH:MM:SS) ----
(function initClock() {
  const el = document.getElementById("clock");
  if (!el) return;
  const pad = (n) => String(n).padStart(2, "0");
  const tick = () => {
    const d = new Date();
    el.textContent = `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}:${pad(d.getUTCSeconds())} UTC`;
  };
  tick();
  setInterval(tick, 1000);
})();

// ---- Scroll progress bar ----
(function initProgress() {
  const el = document.getElementById("progressBar");
  if (!el) return;
  let raf = 0;
  const update = () => {
    const h = document.documentElement;
    const max = h.scrollHeight - h.clientHeight;
    const p = max > 0 ? (h.scrollTop / max) * 100 : 0;
    el.style.setProperty("--p", p.toFixed(2) + "%");
    raf = 0;
  };
  window.addEventListener("scroll", () => {
    if (!raf) raf = requestAnimationFrame(update);
  }, { passive: true });
  update();
})();


async function sendImage() {
  const AZURE_KEY = window.CONFIG.QUEENS_AZURE_API_KEY;
  const input = document.getElementById("imageInput");
  const status = document.getElementById("uploadStatus");

  const usingDefault = !input.files.length;
  let file = null;

  let imageBuffer;
  if (usingDefault) {
    status.textContent = "NO FILE — USING DEFAULT BOARD";
    const response = await fetch("assets/queens.jpeg");
    imageBuffer = await response.arrayBuffer();
  } else {
    file = input.files[0];
    status.textContent = "UPLOADING " + file.name.toUpperCase();
  }

  try {
    // Note: CORS must be enabled on the server (Access-Control-Allow-Origin).
    // This client request will use CORS mode and surface clearer messaging
    // if the browser blocks the request due to missing server headers.
    const response = await fetch(
      "https://linkedin-solvers.azurewebsites.net/api/queens/solve?code=" + AZURE_KEY,
      {
        method: "POST",
        mode: "cors",
        headers: {
          "Content-Type": "application/octet-stream"
        },
        body: usingDefault
          ? imageBuffer
          : await file.arrayBuffer()
      }
    );

    if (!response.ok) {
      const txt = await response.text().catch(() => null);
      status.textContent = `REQUEST FAILED — ${response.status}${txt ? ': ' + txt : ''}`.toUpperCase();
      const imgEl = document.getElementById('resultImage');
      imgEl.style.display = 'none';
      return;
    }

    const contentType = (response.headers.get('content-type') || '').toLowerCase();
    const imgEl = document.getElementById('resultImage');

    if (contentType.startsWith('image/')) {
      const blob = await response.blob();
      // revoke previous url
      if (_lastResultObjectUrl) {
        URL.revokeObjectURL(_lastResultObjectUrl);
        _lastResultObjectUrl = null;
      }
      const objectUrl = URL.createObjectURL(blob);
      _lastResultObjectUrl = objectUrl;
      imgEl.src = objectUrl;
      imgEl.style.display = 'block';
      status.textContent = 'SOLVED — BOARD RECEIVED';
    } else {
      const text = await response.text().catch(() => null);
      imgEl.style.display = 'none';
      status.textContent = text ? `RESPONSE — ${text}`.toUpperCase() : 'REQUEST COMPLETE';
    }
  } catch (err) {
    status.textContent =
      err instanceof TypeError
        ? "CORS / NETWORK ERROR — CHECK SERVER ORIGIN"
        : "ERROR SENDING IMAGE";
    console.error(err);
  }
}

/* ---------- Service Worker registration ---------- */
(function registerServiceWorker() {
  try {
    if (!('serviceWorker' in navigator)) return;
    const proto = window.location.protocol;
    const host = window.location.hostname;
    const isLocalhost = host === 'localhost' || host === '127.0.0.1' || host === '[::1]';
    if (proto !== 'https:' && !isLocalhost) return;

    window.addEventListener('load', function () {
      try {
        navigator.serviceWorker.register('/sw.js').catch(function () { /* silent */ });
      } catch (_) { /* silent */ }
    });
  } catch (_) { /* silent */ }
})();
