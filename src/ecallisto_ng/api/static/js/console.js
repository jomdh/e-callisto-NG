// Generic management console: a config-driven CRUD island over the API.
// CSP-safe (external file, same-origin fetch with the session cookie, no inline
// handlers). The page sets data-resource on #console.
(function () {
  "use strict";
  const root = document.getElementById("console");
  if (!root) return;

  const SELECT = {
    role: ["viewer", "operator", "admin"],
    instrument_class: ["heterodyne", "sdr_soft", "sdr_fpga"],
    unit: ["raw", "sfu", "kelvin"],
    output_mode: ["standard", "legacy"],
    kind: ["sun", "fixed"],
    protocol: ["local", "ftp", "sftp"],
    dispatch: ["manual", "immediate", "scheduled"],
  };

  const RESOURCES = {
    instruments: {
      title: "Instruments",
      scan: true,
      list: "/api/v1/instruments",
      create: "/api/v1/instruments",
      del: (r) => `/api/v1/instruments/${r.id}`,
      columns: ["id", "name", "instrument_class", "channels", "unit", "enabled"],
      fields: [
        { name: "name", required: true },
        { name: "instrument_class", select: "instrument_class" },
        { name: "channels", type: "number", value: 200 },
        { name: "sweep_rate_hz", type: "number", value: 4 },
        { name: "address", placeholder: "serial/host:port (blank=fake)" },
        { name: "unit", select: "unit" },
        { name: "output_mode", select: "output_mode" },
        { name: "file_seconds", type: "number", value: 900 },
      ],
      actions: [
        { label: "open", href: (r) => `/portal/instruments/${r.id}` },
        { label: "record", run: (r) => api("POST", `/api/v1/instruments/${r.id}/record?frames=200`) },
        { label: "stop", run: (r) => api("POST", `/api/v1/instruments/${r.id}/stop`) },
        { label: "live", href: (r) => `/portal/live/${r.id}` },
      ],
    },
    schedules: {
      title: "Schedules",
      list: "/api/v1/schedules",
      create: "/api/v1/schedules",
      del: (r) => `/api/v1/schedules/${r.id}`,
      columns: ["id", "instrument_id", "kind", "margin_minutes", "start_utc", "stop_utc", "program_id", "overview_at", "enabled"],
      fields: [
        { name: "instrument_id", type: "number", required: true },
        { name: "kind", select: "kind" },
        { name: "margin_minutes", type: "number", value: 0 },
        { name: "start_utc", value: "00:00" },
        { name: "stop_utc", value: "23:59" },
        { name: "program_id", type: "number", placeholder: "program to record (blank=ramp)" },
        { name: "overview_at", placeholder: "HH:MM scheduled overview (blank=none)" },
      ],
      actions: [
        { label: "preview", run: (r) => api("GET", `/api/v1/schedules/${r.id}/preview`), show: true },
      ],
    },
    programs: {
      title: "Frequency programs",
      list: "/api/v1/programs",
      create: "/api/v1/programs",
      del: (r) => `/api/v1/programs/${r.id}`,
      columns: ["id", "name", "start_mhz", "stop_mhz", "source"],
      fields: [
        { name: "name", required: true },
        { name: "frequencies", json: true, placeholder: "[45.0, 55.0, 65.0]" },
        { name: "light_curve_indices", json: true, placeholder: "[0, 2] (channel indices, max 10)" },
        { name: "start_mhz", type: "number", value: 45 },
        { name: "stop_mhz", type: "number", value: 870 },
      ],
    },
    calibration: {
      title: "Calibration sets",
      list: "/api/v1/calibration",
      create: "/api/v1/calibration",
      del: (r) => `/api/v1/calibration/${r.id}`,
      columns: ["id", "name"],
      fields: [
        { name: "name", required: true },
        { name: "coefficients", json: true, placeholder: "[[10,40,1,2.7]]" },
      ],
    },
    uploads: {
      title: "Upload targets",
      list: "/api/v1/upload/targets",
      create: "/api/v1/upload/targets",
      columns: ["id", "name", "protocol", "host", "dispatch", "enabled", "has_password"],
      fields: [
        { name: "name", required: true },
        { name: "protocol", select: "protocol" },
        { name: "host", placeholder: "dir (local) or ftp host" },
        { name: "base_path", value: "/" },
        { name: "username" },
        { name: "password", type: "password" },
        { name: "dispatch", select: "dispatch" },
      ],
      actions: [
        { label: "run", run: (r) => api("POST", `/api/v1/upload/targets/${r.id}/run`), show: true },
        { label: "test", run: (r) => api("POST", `/api/v1/upload/targets/${r.id}/test`), show: true },
      ],
    },
    users: {
      title: "Users",
      list: "/api/v1/users",
      create: "/api/v1/users",
      del: (r) => `/api/v1/users/${r.id}`,
      columns: ["id", "username", "role", "active"],
      fields: [
        { name: "username", required: true },
        { name: "password", type: "password", required: true },
        { name: "role", select: "role" },
      ],
    },
    peers: {
      title: "Fleet peers",
      list: "/api/v1/fleet/peers",
      create: "/api/v1/fleet/peers",
      del: (r) => `/api/v1/fleet/peers/${r.id}`,
      columns: ["id", "name", "base_url", "enabled"],
      fields: [
        { name: "name", required: true },
        { name: "base_url", required: true, placeholder: "https://stn2.example" },
        { name: "token" },
      ],
    },
  };

  const cfg = RESOURCES[root.dataset.resource];
  if (!cfg) {
    root.textContent = "Unknown resource.";
    return;
  }

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

  function el(tag, attrs, ...kids) {
    const e = document.createElement(tag);
    for (const k in (attrs || {})) e.setAttribute(k, attrs[k]);
    for (const c of kids) if (c != null) e.append(c.nodeType ? c : String(c));
    return e;
  }

  const out = el("pre", { class: "muted", style: "white-space:pre-wrap" });

  function note(msg, cls) {
    out.className = cls || "muted";
    out.textContent = typeof msg === "string" ? msg : JSON.stringify(msg, null, 2);
  }

  async function refresh() {
    let rows;
    try { rows = await api("GET", cfg.list); } catch (e) { return note(e.message, "error"); }
    const table = el("table");
    const thead = el("tr");
    cfg.columns.forEach((c) => thead.append(el("th", {}, c)));
    if (cfg.actions || cfg.del) thead.append(el("th", {}, ""));
    table.append(thead);
    rows.forEach((r) => {
      const tr = el("tr");
      cfg.columns.forEach((c) => tr.append(el("td", {}, fmt(r[c]))));
      const td = el("td", {});
      (cfg.actions || []).forEach((a) => {
        if (a.href) {
          td.append(el("a", { href: a.href(r), style: "margin-right:.6em" }, a.label));
        } else {
          const b = el("button", { class: "btn-text", style: "margin-right:.4em;padding:.2em .6em" }, a.label);
          b.addEventListener("click", async () => {
            try { const res = await a.run(r); note(a.show ? res : `${a.label}: ok`, "ok"); refresh(); }
            catch (e) { note(e.message, "error"); }
          });
          td.append(b);
        }
      });
      if (cfg.del) {
        const d = el("button", { class: "btn-text", style: "padding:.2em .6em" }, "delete");
        d.addEventListener("click", async () => {
          try { await api("DELETE", cfg.del(r)); refresh(); } catch (e) { note(e.message, "error"); }
        });
        td.append(d);
      }
      tr.append(td);
      table.append(tr);
    });
    body.replaceChildren(table);
    if (!rows.length) body.append(el("p", { class: "muted" }, "None yet."));
  }

  function fmt(v) {
    if (v == null) return "";
    if (typeof v === "boolean") return v ? "yes" : "no";
    return String(v);
  }

  const body = el("div", {});
  const form = el("form", {});
  cfg.fields.forEach((f) => {
    form.append(el("label", { for: f.name }, f.name));
    let input;
    if (f.select) {
      input = el("select", { id: f.name, name: f.name });
      SELECT[f.select].forEach((o) => input.append(el("option", {}, o)));
    } else if (f.json) {
      input = el("textarea", { id: f.name, name: f.name, rows: "2", placeholder: f.placeholder || "" });
    } else {
      input = el("input", { id: f.name, name: f.name, type: f.type || "text" });
      if (f.value != null) input.value = f.value;
      if (f.placeholder) input.placeholder = f.placeholder;
    }
    form.append(input);
  });
  const submit = el("button", { class: "btn-filled", type: "submit", style: "margin-top:1rem" }, "Create");
  form.append(submit);

  // Device scanner: detect hardware and fill the form for a chosen device.
  // Several devices on one station are each selectable (by their address).
  function scanPanel() {
    const panel = el("div", { class: "data-toolbar", style: "margin-bottom:.75rem" });
    const btn = el("button", { class: "btn-filled", type: "button" }, "Scan for devices");
    const sel = el("select", { id: "scan-pick", style: "min-width:18em" });
    sel.append(el("option", { value: "" }, "-- detected devices --"));
    const useBtn = el("button", { class: "btn-text", type: "button" }, "use selected");
    const msg = el("span", { class: "muted" });
    let devices = [];
    btn.addEventListener("click", async () => {
      msg.textContent = "scanning + probing...";
      try {
        const d = await api("GET", "/api/v1/discovery/scan?probe=true");
        devices = d.devices || [];
        sel.replaceChildren(el("option", { value: "" }, `-- ${d.count} device(s) --`));
        devices.forEach((dev, i) => {
          const lbl = `${dev.address} — ${dev.detail || dev.description} [${dev.suggested_class}]`;
          sel.append(el("option", { value: String(i) }, lbl));
        });
        msg.textContent = d.count ? "pick a device, then 'use selected'" : "none found";
      } catch (e) { msg.textContent = e.message; }
    });
    useBtn.addEventListener("click", () => {
      if (sel.value === "") return;
      const dev = devices[Number(sel.value)];
      if (!dev) return;
      if (form.elements.instrument_class) form.elements.instrument_class.value = dev.suggested_class;
      // keep the address for both serial (/dev/tty…) and USB (usb:vid:pid) so
      // the driver can route (e.g. an RX-888 by its USB id).
      if (form.elements.address) form.elements.address.value = dev.address;
      if (form.elements.name && !form.elements.name.value) {
        form.elements.name.value = dev.kind === "serial" ? "Callisto" : "SDR";
      }
      msg.textContent = `filled from ${dev.address}`;
    });
    panel.append(btn, sel, useBtn, msg);
    return panel;
  }
  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const payload = {};
    cfg.fields.forEach((f) => {
      const v = form.elements[f.name].value;
      if (f.json) payload[f.name] = v ? JSON.parse(v) : [];
      else if (f.type === "number") {
        if (v !== "") payload[f.name] = Number(v); // blank -> server default
      } else payload[f.name] = v;
    });
    try { await api("POST", cfg.create, payload); form.reset(); note("created", "ok"); refresh(); }
    catch (e) { note(e.message, "error"); }
  });

  const card = el("div", { class: "card", style: "margin-bottom:1rem" });
  if (cfg.scan) card.append(scanPanel());
  card.append(form);
  root.replaceChildren(card, body, out);
  refresh();
})();
