// Per-instrument device console: operate actions + bench/NF (heterodyne).
// CSP-safe external file; reuses the existing per-instrument endpoints.
// One serial device = one operation at a time: while an op runs (or a
// recording is active) the other controls are disabled so two can't collide.
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
  const actBtns = Array.from(root.querySelectorAll("button[data-act]"));
  const stopBtn = root.querySelector('button[data-act="stop"]');
  const benchBtns = [$("d-read"), $("d-nf")].filter(Boolean);
  const allBtns = actBtns.concat(benchBtns); // every port-touching control
  let inFlight = false;

  function setEnabled(btn, on) {
    if (!btn) return;
    btn.disabled = !on;
    btn.style.opacity = on ? "" : "0.4";
    btn.style.pointerEvents = on ? "" : "none";
  }

  function lockAll() {
    allBtns.forEach((b) => setEnabled(b, false));
  }

  // Apply the idle/recording state to the controls (skipped while an op is
  // mid-flight, so the lock holds until it returns).
  function applyState(state) {
    if (inFlight) return;
    if (state === "recording") {
      allBtns.forEach((b) => setEnabled(b, b === stopBtn));
    } else {
      allBtns.forEach((b) => setEnabled(b, true));
    }
  }

  // Run one operation with the whole console locked, then re-evaluate state.
  async function runOp(fn) {
    if (inFlight) return;
    inFlight = true;
    lockAll();
    try { await fn(); } finally { inFlight = false; await refresh(); }
  }

  const ACTIONS = {
    record: ["POST", `/api/v1/instruments/${id}/record`],
    stop: ["POST", `/api/v1/instruments/${id}/stop`],
    overview: ["POST", `/api/v1/instruments/${id}/overview`],
    diagnose: ["GET", `/api/v1/instruments/${id}/diagnose`],
    reconnect: ["POST", `/api/v1/instruments/${id}/reconnect`],
  };
  actBtns.forEach((b) => {
    b.addEventListener("click", () =>
      runOp(async () => {
        const a = ACTIONS[b.dataset.act];
        if (!a) return;
        out.textContent = b.dataset.act + "...";
        try {
          out.textContent = JSON.stringify(await api(a[0], a[1]), null, 2);
        } catch (e) {
          out.textContent = e.message;
        }
      })
    );
  });

  // bench detector
  if ($("d-read")) {
    $("d-read").addEventListener("click", () =>
      runOp(async () => {
        const f = $("d-freq").value, g = $("d-gain").value;
        $("d-mv").textContent = "reading...";
        try {
          const r = await api(
            "GET",
            `/api/v1/instruments/${id}/bench/detector?freq=${f}&gain=${g}`
          );
          $("d-mv").textContent = `${r.mv} mV`;
        } catch (e) { $("d-mv").textContent = e.message; }
      })
    );
  }

  // noise figure
  if ($("d-nf")) {
    $("d-nf").addEventListener("click", () =>
      runOp(async () => {
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
      })
    );
  }

  // live status chip + control state (also catches an external recording)
  async function refresh() {
    try {
      const s = await api("GET", `/api/v1/instruments/${id}/status`);
      const chip = $("d-state");
      if (chip) chip.textContent = inFlight ? "busy" : s.state;
      applyState(s.state);
    } catch (e) { /* ignore */ }
  }
  refresh();
  setInterval(refresh, 5000);
})();
