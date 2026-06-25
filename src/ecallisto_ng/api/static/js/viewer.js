// Spectrum viewer island (legacy M9703APlotter parity): LO conversion, dB/log,
// background subtraction, typed-range zoom, PNG export. Theme-coloured.
// CSP-safe (external file, same-origin fetch with the session cookie).
(function () {
  "use strict";
  const canvas = document.getElementById("v-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const msg = document.getElementById("v-msg");

  const $ = (id) => document.getElementById(id);
  let raw = { freqs: [], amps: [] };

  function themed(name, fallback) {
    const v = getComputedStyle(document.documentElement)
      .getPropertyValue(name)
      .trim();
    return v || fallback;
  }

  async function api(url) {
    const r = await fetch(url);
    const t = await r.text();
    let d;
    try { d = JSON.parse(t); } catch (e) { d = t; }
    if (!r.ok) throw new Error((d && d.detail) || r.status);
    return d;
  }

  function transform() {
    const lo = Number($("v-lo").value) || 0;
    const mode = $("v-lo-mode").value;
    const freqs = raw.freqs.map((f) => {
      if (mode === "add") return lo + f;
      if (mode === "sub") return lo - f;
      if (mode === "rev") return f - lo;
      return f;
    });
    let amps = raw.amps.slice();
    if ($("v-db").checked) amps = amps.map((a) => 10 * Math.log10(Math.max(a, 1e-6)));
    if ($("v-bg").checked) {
      const lo2 = Math.min(...amps);
      amps = amps.map((a) => a - lo2);
    }
    return { freqs, amps };
  }

  function draw() {
    const data = transform();
    const W = canvas.width, H = canvas.height;
    const padL = 54, padB = 30, padT = 14, padR = 12;
    ctx.fillStyle = themed("--surface", "#10131c");
    ctx.fillRect(0, 0, W, H);
    if (!data.freqs.length) { msg.textContent = "no data"; return; }

    const xmin = $("v-xmin").value !== "" ? Number($("v-xmin").value) : Math.min(...data.freqs);
    const xmax = $("v-xmax").value !== "" ? Number($("v-xmax").value) : Math.max(...data.freqs);
    const ymin = Math.min(...data.amps), ymax = Math.max(...data.amps) || 1;
    const px = (f) => padL + ((f - xmin) / (xmax - xmin || 1)) * (W - padL - padR);
    const py = (a) => H - padB - ((a - ymin) / (ymax - ymin || 1)) * (H - padT - padB);

    ctx.strokeStyle = themed("--border", "#333");
    ctx.strokeRect(padL, padT, W - padL - padR, H - padT - padB);
    ctx.fillStyle = themed("--fg-muted", "#9aa");
    ctx.font = "11px sans-serif";
    ctx.fillText("Frequency [MHz]", W / 2 - 40, H - 6);
    ctx.fillText($("v-db").checked ? "dB" : "amplitude", 4, padT + 10);

    ctx.strokeStyle = themed("--accent", "#7bd");
    ctx.beginPath();
    data.freqs.forEach((f, i) => {
      if (f < xmin || f > xmax) return;
      const x = px(f), y = py(data.amps[i]);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.stroke();
    msg.textContent = `${data.freqs.length} points`;
  }

  async function load(name) {
    if (!name) return;
    try {
      raw = await api(`/api/v1/spectra/${encodeURIComponent(name)}`);
      $("v-xmin").value = "";
      $("v-xmax").value = "";
      draw();
    } catch (e) { msg.textContent = e.message; }
  }

  ["v-lo-mode", "v-lo", "v-db", "v-bg", "v-xmin", "v-xmax"].forEach((id) =>
    $(id).addEventListener("input", draw)
  );
  $("v-file").addEventListener("change", (e) => load(e.target.value));
  $("v-png").addEventListener("click", () => {
    const a = document.createElement("a");
    a.href = canvas.toDataURL("image/png");
    a.download = ($("v-file").value || "spectrum") + ".png";
    a.click();
  });

  api("/api/v1/spectra").then((names) => {
    const sel = $("v-file");
    names.forEach((n) => {
      const o = document.createElement("option");
      o.value = n;
      o.textContent = n;
      sel.append(o);
    });
    if (names.length) load(names[names.length - 1]);
    else msg.textContent = "No spectrum files yet (run an overview).";
  }).catch((e) => { msg.textContent = e.message; });
})();
