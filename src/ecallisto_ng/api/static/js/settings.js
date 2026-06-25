// Handlers for the dedicated settings pages (access / import / fleet).
// CSP-safe: external file, same-origin fetch with the session cookie.
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

  // ---- access settings -------------------------------------------------
  const accessForm = document.getElementById("access-form");
  if (accessForm) {
    const msg = document.getElementById("access-msg");
    const fields = ["mode", "hostname", "tls_email", "ddns_update_url", "tunnel_relay"];
    api("GET", "/api/v1/access").then((cur) => {
      fields.forEach((f) => { if (cur[f] != null) accessForm.elements[f].value = cur[f]; });
    }).catch((e) => { msg.textContent = e.message; });
    accessForm.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const payload = {};
      fields.forEach((f) => { payload[f] = accessForm.elements[f].value; });
      try { await api("PUT", "/api/v1/access", payload); msg.textContent = "saved"; }
      catch (e) { msg.textContent = e.message; }
    });
  }

  // ---- legacy import ---------------------------------------------------
  const importForm = document.getElementById("import-form");
  if (importForm) {
    const msg = document.getElementById("import-msg");
    importForm.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const payload = {
        callisto_cfg: importForm.elements.callisto_cfg.value,
        frq_cfg: importForm.elements.frq_cfg.value,
        scheduler_cfg: importForm.elements.scheduler_cfg.value,
        cal_prn: importForm.elements.cal_prn.value,
        dry_run: importForm.elements.dry_run.checked,
      };
      try {
        const res = await api("POST", "/api/v1/import", payload);
        msg.textContent = JSON.stringify(res, null, 2);
      } catch (e) { msg.textContent = e.message; }
    });
  }

  // ---- audit log -------------------------------------------------------
  const auditView = document.getElementById("audit-view");
  if (auditView) {
    api("GET", "/api/v1/audit").then((rows) => {
      const table = document.createElement("table");
      const head = document.createElement("tr");
      ["when", "actor", "action", "target", "detail"].forEach((c) => {
        const th = document.createElement("th");
        th.textContent = c;
        head.append(th);
      });
      table.append(head);
      rows.forEach((r) => {
        const tr = document.createElement("tr");
        [r.created_at, r.actor, r.action, r.target, r.detail].forEach((v) => {
          const td = document.createElement("td");
          td.textContent = v == null ? "" : String(v);
          tr.append(td);
        });
        table.append(tr);
      });
      auditView.replaceChildren(table);
      if (!rows.length) auditView.textContent = "No events yet.";
    }).catch((e) => { auditView.textContent = e.message; });
  }

  // ---- fleet aggregate -------------------------------------------------
  const fleetView = document.getElementById("fleet-view");
  if (fleetView) {
    api("GET", "/api/v1/fleet").then((data) => {
      const self = data.self || {};
      const rows = [["this station", true, self.disk_pct_free, (self.alerts || []).length]];
      (data.peers || []).forEach((p) => {
        const h = p.health || {};
        rows.push([p.name, p.reachable, h.disk_pct_free, (h.alerts || []).length]);
      });
      const table = document.createElement("table");
      const head = document.createElement("tr");
      ["station", "reachable", "disk % free", "alerts"].forEach((c) => {
        const th = document.createElement("th"); th.textContent = c; head.append(th);
      });
      table.append(head);
      rows.forEach((r) => {
        const tr = document.createElement("tr");
        r.forEach((v, i) => {
          const td = document.createElement("td");
          td.textContent = i === 1 ? (v ? "yes" : "no") : (v == null ? "" : String(v));
          tr.append(td);
        });
        table.append(tr);
      });
      fleetView.replaceChildren(table);
    }).catch((e) => { fleetView.textContent = e.message; });
  }
})();
