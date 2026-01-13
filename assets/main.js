// Scripts extracted from index.html
window.CONFIG = {
  QUEENS_AZURE_API_KEY: "__QUEENS_AZURE_API_KEY__",
  VOL_AZURE_API_KEY: "__VOL_AZURE_API_KEY__"
};

// Track last created object URL so we can revoke it when replaced
let _lastResultObjectUrl = null;

// // Set an example volatility-surface iframe on page load (example: TSLA)
// document.addEventListener("DOMContentLoaded", function () {
//   const AZURE_KEY = window.CONFIG.VOL_AZURE_API_KEY;
//   const iframe = document.getElementById("volIframe");
//   const defaultSymbol = "TSLA";
//
//   const BASE_VOL_URL =
//     "https://volsurface.azurewebsites.net/api/volatility-surface?code=" +
//     AZURE_KEY +
//     "&ticker=";
//
//   // Set the iframe src so an example is already requested on load
//   iframe.src = BASE_VOL_URL + defaultSymbol;
// });

async function sendImage() {
  const AZURE_KEY = window.CONFIG.QUEENS_AZURE_API_KEY;
  const input = document.getElementById("imageInput");
  const status = document.getElementById("uploadStatus");

  const usingDefault = !input.files.length;
  let file = null;

  let imageBuffer;
  if (usingDefault) {
    status.textContent = "No file selected — using default image.";
    const response = await fetch("assets/queens.jpeg");
    imageBuffer = await response.arrayBuffer();
  } else {
    file = input.files[0];
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
      status.textContent = `Request failed (status ${response.status})${txt ? ': ' + txt : ''}`;
      // hide previous image if any
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
      status.textContent = 'Image received.';
    } else {
      // Not an image — show textual response
      const text = await response.text().catch(() => null);
      imgEl.style.display = 'none';
      status.textContent = text ? `Response: ${text}` : 'Request completed.';
    }
  } catch (err) {
    // A TypeError here often indicates a CORS/network failure in the browser.
    status.textContent =
      err instanceof TypeError
        ? "CORS or network error. Ensure server allows this origin."
        : "Error sending image.";
    console.error(err);
  }
}

function updateIframe() {
  const AZURE_KEY = window.CONFIG.VOL_AZURE_API_KEY;
  const input = document.getElementById("symbolInput");
  const iframe = document.getElementById("volIframe");

  if (!input.value.trim()) return;

  const symbol = input.value.trim().toUpperCase();

  const BASE_VOL_URL =
    "https://volsurface.azurewebsites.net/api/volatility-surface?code=" +
    AZURE_KEY +
    "&ticker=";

  iframe.src = BASE_VOL_URL + symbol;
  const visitLink = document.getElementById('volVisitLink');
  if (visitLink) {
    visitLink.href = BASE_VOL_URL + symbol;
    visitLink.style.display = 'block';
  }
}
