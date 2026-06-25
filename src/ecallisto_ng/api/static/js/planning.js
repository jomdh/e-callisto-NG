// Planning panel: source az/el track vs horizon. CSP-safe external file.
(function () {
  "use strict";
  const canvas = document.getElementById("pl-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const $ = (id) => document.getElementById(id);

  function themed(name, fallback) {
    return (
      getComputedStyle(document.documentElement)
        .getPropertyValue(name)
        .trim() || fallback
    );
  }

  async function api(url) {
    const r = await fetch(url);
    const d = await r.json();
    if (!r.ok) throw new Error(d.detail || r.status);
    return d;
  }

  function draw(data) {
    const W = canvas.width, H = canvas.height;
    const padL = 40, padB = 28, padT = 12, padR = 12;
    ctx.fillStyle = themed("--surface", "#10131c");
    ctx.fillRect(0, 0, W, H);
    const x = (h) => padL + (h / 24) * (W - padL - padR);
    const y = (el) => H - padB - ((el + 90) / 180) * (H - padT - padB);

    // axes + horizon (el=0) + station horizon line
    ctx.strokeStyle = themed("--border", "#333");
    ctx.strokeRect(padL, padT, W - padL - padR, H - padT - padB);
    ctx.fillStyle = themed("--fg-muted", "#9aa");
    ctx.font = "11px sans-serif";
    [0, 6, 12, 18, 24].forEach((h) => {
      ctx.fillText(h + "h", x(h) - 6, H - 8);
    });
    ctx.strokeStyle = themed("--fg-muted", "#9aa");
    ctx.beginPath();
    ctx.moveTo(padL, y(0));
    ctx.lineTo(W - padR, y(0));
    ctx.stroke();
    ctx.fillText("horizon", padL + 4, y(0) - 3);
    if (data.horizon_deg) {
      ctx.strokeStyle = themed("--warn", "#e0a000");
      ctx.beginPath();
      ctx.moveTo(padL, y(data.horizon_deg));
      ctx.lineTo(W - padR, y(data.horizon_deg));
      ctx.stroke();
    }

    // source elevation track
    ctx.strokeStyle = themed("--accent", "#7bd");
    ctx.beginPath();
    data.track.forEach((p, i) => {
      const px = x(p[0]), py = y(p[2]);
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    });
    ctx.stroke();
    $("pl-msg").textContent =
      "max elevation " +
      Math.max(...data.track.map((p) => p[2])).toFixed(1) + " deg";
  }

  function refresh() {
    const src = $("pl-source").value || "sun";
    const day = $("pl-date").value;
    api(`/api/v1/planning/track?source=${src}&day=${day}`)
      .then(draw)
      .catch((e) => { $("pl-msg").textContent = e.message; });
  }

  // init: populate sources + today, then draw
  $("pl-date").value = new Date().toISOString().slice(0, 10);
  api("/api/v1/planning/track?source=sun").then((data) => {
    const sel = $("pl-source");
    data.sources.forEach((s) => {
      const o = document.createElement("option");
      o.value = s;
      o.textContent = s;
      sel.append(o);
    });
    draw(data);
  }).catch((e) => { $("pl-msg").textContent = e.message; });

  $("pl-source").addEventListener("change", refresh);
  $("pl-date").addEventListener("change", refresh);
})();
