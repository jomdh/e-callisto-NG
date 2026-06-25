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

  // ---- station settings (system info + config backup/restore) ---------
  const sysinfo = document.getElementById("sysinfo");
  if (sysinfo) {
    api("GET", "/api/v1/system/info").then((i) => {
      const gb = (n) => (n / 1e9).toFixed(1) + " GB";
      sysinfo.textContent =
        `version ${i.version}\n` +
        `disk ${gb(i.disk_free)} free of ${gb(i.disk_total)} ` +
        `(${i.disk_pct_free}%)\n` +
        `clock synced: ${i.clock_synced}\n` +
        `retention: ${i.retention_days} days` +
        (i.archive_dir ? `  archive: ${i.archive_dir}` : "") +
        `\ndata dir: ${i.data_dir}`;
    }).catch((e) => { sysinfo.textContent = e.message; });
  }

  const cfgExport = document.getElementById("cfg-export");
  if (cfgExport) {
    const cmsg = document.getElementById("cfg-msg");
    cfgExport.addEventListener("click", async () => {
      try {
        const cfg = await api("GET", "/api/v1/config/export");
        const blob = new Blob([JSON.stringify(cfg, null, 2)], {
          type: "application/json",
        });
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = "ecallisto-config.json";
        a.click();
      } catch (e) { cmsg.textContent = e.message; }
    });
    document.getElementById("cfg-import").addEventListener("click", async () => {
      try {
        const data = JSON.parse(document.getElementById("cfg-text").value);
        const res = await api("POST", "/api/v1/config/import", data);
        cmsg.textContent = "restored: " + JSON.stringify(res);
      } catch (e) { cmsg.textContent = e.message; }
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
