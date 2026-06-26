// Diagnostics page: run the station self-check and render the results.
// CSP-safe external file; addEventListener only.
(function () {
  "use strict";
  const checksEl = document.getElementById("dg-checks");
  const overallEl = document.getElementById("dg-overall");
  const runBtn = document.getElementById("dg-run");
  if (!checksEl) return;

  const DOT = { ok: "●", warn: "▲", fail: "✕" };
  const COLOR = { ok: "#3ddc84", warn: "#ffb454", fail: "#ff5a5a" };

  async function run() {
    overallEl.textContent = "checking…";
    checksEl.replaceChildren();
    let data;
    try {
      const r = await fetch("/api/v1/diagnostics");
      if (!r.ok) throw new Error(r.status);
      data = await r.json();
    } catch (e) {
      overallEl.textContent = "error: " + e.message;
      return;
    }
    const o = data.status;
    overallEl.textContent =
      o === "ok" ? "all clear" : o === "warn" ? "warnings found" : "problems found";
    overallEl.style.color = COLOR[o] || "";
    (data.checks || []).forEach((c) => {
      const row = document.createElement("div");
      row.style.cssText =
        "display:flex;gap:.6em;align-items:baseline;padding:.3em 0;border-bottom:1px solid rgba(255,255,255,.06)";
      const dot = document.createElement("span");
      dot.textContent = DOT[c.status] || "?";
      dot.style.color = COLOR[c.status] || "";
      const name = document.createElement("strong");
      name.textContent = c.name;
      name.style.minWidth = "12em";
      const detail = document.createElement("span");
      detail.className = "muted";
      detail.textContent = c.detail;
      row.append(dot, name, detail);
      checksEl.append(row);
    });
  }

  runBtn.addEventListener("click", run);
  run();
})();
