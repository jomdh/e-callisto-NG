// Live waterfall island: stream 8-bit spectra over WS, scroll a canvas.
(function () {
  "use strict";
  const canvas = document.getElementById("waterfall");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const status = document.getElementById("live-status");
  const id = canvas.dataset.instrument;
  const W = canvas.width;
  const H = canvas.height;

  // simple blue->cyan->white colormap for an 8-bit value
  function color(v) {
    const r = v < 128 ? 0 : (v - 128) * 2;
    const g = v < 64 ? v * 2 : 255;
    const b = v < 64 ? 128 + v * 2 : 255 - (v - 64);
    return "rgb(" + r + "," + g + "," + Math.max(0, b) + ")";
  }

  function drawColumn(values) {
    // scroll left by 1px
    const img = ctx.getImageData(1, 0, W - 1, H);
    ctx.putImageData(img, 0, 0);
    const n = values.length;
    for (let i = 0; i < n; i++) {
      const y0 = Math.floor((i / n) * H);
      const y1 = Math.floor(((i + 1) / n) * H);
      ctx.fillStyle = color(values[i] & 0xff);
      ctx.fillRect(W - 1, y0, 1, Math.max(1, y1 - y0));
    }
  }

  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(proto + "://" + location.host + "/ws/live/" + id);
  ws.onopen = function () {
    if (status) status.textContent = "live";
  };
  ws.onclose = function () {
    if (status) status.textContent = "disconnected";
  };
  ws.onmessage = function (ev) {
    const msg = JSON.parse(ev.data);
    if (msg.values) drawColumn(msg.values);
  };
})();
