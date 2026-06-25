// Bench tools island: detector readout + Y-factor noise figure.
// CSP-safe (external file, same-origin fetch with the session cookie).
(function () {
  "use strict";

  async function api(method, url, body) {
    const opts = { method, headers: {} };
    if (body !== undefined) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
    const resp = await fetch(url, opts);
    const text = await resp.text();
    let data;
    try { data = JSON.parse(text); } catch (e) { data = text; }
    if (!resp.ok) throw new Error((data && data.detail) || resp.status);
    return data;
  }

  const readBtn = document.getElementById("bench-read");
  if (readBtn) {
    const gauge = document.getElementById("bench-gauge");
    const mv = document.getElementById("bench-mv");
    readBtn.addEventListener("click", async () => {
      const id = document.getElementById("bench-inst").value;
      const f = document.getElementById("bench-freq").value;
      const g = document.getElementById("bench-gain").value;
      mv.textContent = "reading...";
      try {
        const r = await api(
          "GET",
          `/api/v1/instruments/${id}/bench/detector?freq=${f}&gain=${g}`
        );
        // legacy detector range ~0-2500 mV
        const pct = Math.max(0, Math.min(100, (r.mv / 2500) * 100));
        gauge.style.width = pct + "%";
        mv.textContent = `${r.mv} mV`;
      } catch (e) { mv.textContent = e.message; }
    });
  }

  const nfBtn = document.getElementById("nf-run");
  if (nfBtn) {
    const out = document.getElementById("nf-out");
    nfBtn.addEventListener("click", async () => {
      const id = document.getElementById("nf-inst").value;
      out.textContent = "running cold/warm/hot sweeps...";
      try {
        const r = await api(
          "POST",
          `/api/v1/instruments/${id}/bench/noise_figure`,
          {
            n_points: Number(document.getElementById("nf-n").value),
            enr_db: Number(document.getElementById("nf-enr").value),
            att_db: Number(document.getElementById("nf-att").value),
          }
        );
        out.textContent =
          `NF mean = ${r.nf_mean} dB  (1s = ${r.nf_sigma} dB)\n` +
          `points = ${r.freqs.length}, ` +
          `band ${r.freqs[0].toFixed(1)}-` +
          `${r.freqs[r.freqs.length - 1].toFixed(1)} MHz`;
      } catch (e) { out.textContent = e.message; }
    });
  }
})();
