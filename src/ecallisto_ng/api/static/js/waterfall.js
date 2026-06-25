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

  // --- live panels: single spectrum y(f) + light-curve y(t) -----------
  const dbToggle = document.getElementById("live-db");
  const specCv = document.getElementById("spectrum");
  const lcCv = document.getElementById("lightcurve");
  const lcBuf = [];

  function accent() {
    return (
      getComputedStyle(document.documentElement)
        .getPropertyValue("--accent")
        .trim() || "#7bd"
    );
  }

  function scale(v) {
    return dbToggle && dbToggle.checked
      ? 10 * Math.log10(Math.max(v, 1)) // 0..~24
      : v; // 0..255
  }

  function plot(cv, values, asLine) {
    if (!cv) return;
    const c = cv.getContext("2d");
    const w = cv.width;
    const h = cv.height;
    c.clearRect(0, 0, w, h);
    if (!values.length) return;
    const max = dbToggle && dbToggle.checked ? 24 : 255;
    c.strokeStyle = accent();
    c.beginPath();
    values.forEach((v, i) => {
      const x = (i / (values.length - 1 || 1)) * w;
      const y = h - (Math.min(v, max) / max) * h;
      if (i === 0) c.moveTo(x, y);
      else c.lineTo(x, y);
    });
    c.stroke();
  }

  function updatePanels(values) {
    plot(specCv, values.map(scale));
    let peak = 0;
    for (const v of values) if (v > peak) peak = v;
    lcBuf.push(scale(peak));
    if (lcBuf.length > lcCv.width) lcBuf.shift();
    plot(lcCv, lcBuf);
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
    if (msg.values) {
      drawColumn(msg.values);
      updatePanels(msg.values);
    }
  };
})();
