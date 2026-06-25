// Operations dashboard: per-instrument mini-waterfall (WS) + quick actions +
// periodic cockpit refresh. CSP-safe external file.
(function () {
  "use strict";

  function color(v) {
    const r = v < 128 ? 0 : (v - 128) * 2;
    const g = v < 64 ? v * 2 : 255;
    const b = v < 64 ? 128 + v * 2 : 255 - (v - 64);
    return "rgb(" + r + "," + g + "," + Math.max(0, b) + ")";
  }

  // mini-waterfall per card
  document.querySelectorAll(".cockpit-wf").forEach((canvas) => {
    const ctx = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;
    const id = canvas.dataset.instrument;
    const proto = location.protocol === "https:" ? "wss" : "ws";
    let ws;
    try {
      ws = new WebSocket(proto + "://" + location.host + "/ws/live/" + id);
    } catch (e) { return; }
    ws.onmessage = (ev) => {
      let msg;
      try { msg = JSON.parse(ev.data); } catch (e) { return; }
      if (!msg.values) return;
      const img = ctx.getImageData(1, 0, W - 1, H);
      ctx.putImageData(img, 0, 0);
      const n = msg.values.length;
      for (let i = 0; i < n; i++) {
        const y0 = Math.floor((i / n) * H);
        const y1 = Math.floor(((i + 1) / n) * H);
        ctx.fillStyle = color(msg.values[i] & 0xff);
        ctx.fillRect(W - 1, y0, 1, Math.max(1, y1 - y0));
      }
    };
  });

  // quick actions
  async function act(method, url) {
    const r = await fetch(url, { method });
    return r.ok;
  }
  document.querySelectorAll(".cockpit-actions button[data-act]").forEach((b) => {
    b.addEventListener("click", async () => {
      const id = b.dataset.id, a = b.dataset.act;
      const map = {
        record: ["POST", `/api/v1/instruments/${id}/record?frames=200`],
        stop: ["POST", `/api/v1/instruments/${id}/stop`],
        overview: ["POST", `/api/v1/instruments/${id}/overview`],
      };
      if (!map[a]) return;
      b.disabled = true;
      await act(map[a][0], map[a][1]);
      b.disabled = false;
      refresh();
    });
  });

  // periodic cockpit refresh (state badge + next action)
  async function refresh() {
    try {
      const data = await (await fetch("/api/v1/operations")).json();
      (data.instruments || []).forEach((i) => {
        const card = document.querySelector(
          `.cockpit-card[data-instrument="${i.id}"]`
        );
        if (!card) return;
        const badge = card.querySelector(".cockpit-state");
        if (badge) {
          badge.textContent = i.state;
          badge.dataset.state = i.state;
        }
        const next = card.querySelector('[data-field="next_action"]');
        if (next) next.textContent = i.next_action;
      });
    } catch (e) { /* offline -> keep last */ }
  }
  setInterval(refresh, 10000);
})();
