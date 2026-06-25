// Per-instrument device console: operate actions + bench/NF (heterodyne).
// CSP-safe external file; reuses the existing per-instrument endpoints.
(function () {
  "use strict";
  const root = document.querySelector(".portal-main[data-instrument]");
  if (!root) return;
  const id = root.dataset.instrument;
  const $ = (s) => document.getElementById(s);

  async function api(method, url, body) {
    const opts = { method, headers: {} };
    if (body !== undefined) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
    const r = await fetch(url, opts);
    const t = await r.text();
    let d;
    try { d = JSON.parse(t); } catch (e) { d = t; }
    if (!r.ok) throw new Error((d && d.detail) || r.status);
    return d;
  }

  const out = $("d-out");
  const ACTIONS = {
    record: ["POST", `/api/v1/instruments/${id}/record?frames=200`],
    stop: ["POST", `/api/v1/instruments/${id}/stop`],
    overview: ["POST", `/api/v1/instruments/${id}/overview`],
    diagnose: ["GET", `/api/v1/instruments/${id}/diagnose`],
    reconnect: ["POST", `/api/v1/instruments/${id}/reconnect`],
  };
  root.querySelectorAll("button[data-act]").forEach((b) => {
    b.addEventListener("click", async () => {
      const a = ACTIONS[b.dataset.act];
      if (!a) return;
      out.textContent = b.dataset.act + "...";
      try { out.textContent = JSON.stringify(await api(a[0], a[1]), null, 2); }
      catch (e) { out.textContent = e.message; }
      refresh();
    });
  });

  // bench detector
  if ($("d-read")) {
    $("d-read").addEventListener("click", async () => {
      const f = $("d-freq").value, g = $("d-gain").value;
      $("d-mv").textContent = "reading...";
      try {
        const r = await api(
          "GET",
          `/api/v1/instruments/${id}/bench/detector?freq=${f}&gain=${g}`
        );
        $("d-mv").textContent = `${r.mv} mV`;
      } catch (e) { $("d-mv").textContent = e.message; }
    });
  }

  // noise figure
  if ($("d-nf")) {
    $("d-nf").addEventListener("click", async () => {
      $("d-nfout").textContent = "running cold/warm/hot...";
      try {
        const r = await api(
          "POST",
          `/api/v1/instruments/${id}/bench/noise_figure`,
          {
            n_points: Number($("d-n").value),
            enr_db: Number($("d-enr").value),
          }
        );
        $("d-nfout").textContent = `NF ${r.nf_mean} dB (1s ${r.nf_sigma})`;
      } catch (e) { $("d-nfout").textContent = e.message; }
    });
  }

  // live status chip
  async function refresh() {
    try {
      const s = await api("GET", `/api/v1/instruments/${id}/status`);
      const chip = $("d-state");
      if (chip) chip.textContent = s.state;
    } catch (e) { /* ignore */ }
  }
  refresh();
  setInterval(refresh, 8000);
})();
