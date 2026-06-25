// Hardware discovery: scan for Callisto / SDR and create instruments.
// CSP-safe external file (no inline handlers; event delegation).
(function () {
  "use strict";
  const $ = (s) => document.getElementById(s);
  const rows = $("hw-rows");
  if (!rows) return;

  async function api(method, url, body) {
    const opts = { method, headers: {} };
    if (body !== undefined) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
    const r = await fetch(url, opts);
    const d = await r.json();
    if (!r.ok) throw new Error(d.detail || r.status);
    return d;
  }

  function cell(text) {
    const td = document.createElement("td");
    td.textContent = text;
    return td;
  }

  function render(devices) {
    rows.replaceChildren();
    if (!devices.length) {
      const tr = document.createElement("tr");
      const td = cell("No devices found.");
      td.colSpan = 5;
      td.className = "muted";
      tr.append(td);
      rows.append(tr);
      return;
    }
    devices.forEach((d) => {
      const tr = document.createElement("tr");
      const addr = d.address + (d.callisto ? "  (Callisto)" : "");
      tr.append(cell(addr));
      tr.append(cell(d.detail || d.description));
      tr.append(cell(d.vid ? `${d.vid}:${d.pid}` : "-"));
      tr.append(cell(d.suggested_class));
      const td = document.createElement("td");
      if (d.suggested_class !== "unknown") {
        const btn = document.createElement("button");
        btn.className = "btn-text";
        btn.textContent = "create";
        btn.dataset.create = JSON.stringify({
          name: d.kind === "serial" ? "Callisto" : "SDR",
          instrument_class: d.suggested_class,
          address: d.kind === "serial" ? d.address : "",
        });
        td.append(btn);
      }
      tr.append(td);
      rows.append(tr);
    });
  }

  async function scan(probe) {
    $("hw-msg").textContent = probe ? "scanning + probing..." : "scanning...";
    try {
      const d = await api("GET", `/api/v1/discovery/scan?probe=${!!probe}`);
      render(d.devices);
      $("hw-msg").textContent = `${d.count} device(s)`;
    } catch (e) {
      $("hw-msg").textContent = e.message;
    }
  }

  $("hw-scan").addEventListener("click", () => scan(false));
  $("hw-probe").addEventListener("click", () => scan(true));

  // event delegation for the per-row "create" buttons
  rows.addEventListener("click", async (ev) => {
    const btn = ev.target.closest("button[data-create]");
    if (!btn) return;
    btn.textContent = "...";
    try {
      const body = JSON.parse(btn.dataset.create);
      const inst = await api("POST", "/api/v1/instruments", body);
      window.location.href = `/portal/instruments/${inst.id}`;
    } catch (e) {
      btn.textContent = "create";
      $("hw-msg").textContent = e.message;
    }
  });
})();
