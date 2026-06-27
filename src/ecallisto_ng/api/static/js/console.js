// Generic management console: a config-driven CRUD island over the API.
// CSP-safe (external file, same-origin fetch with the session cookie, no inline
// handlers). Every [data-resource] element on the page becomes an independent
// console; add data-instrument to scope it to one instrument (ADR-0011).
(function () {
  "use strict";
  const mounts = Array.prototype.slice.call(
    document.querySelectorAll("[data-resource]"));
  if (!mounts.length) return;
  mounts.forEach(mountConsole);

  function mountConsole(root) {
  const SELECT = {
    role: ["viewer", "operator", "admin"],
    instrument_class: ["heterodyne", "sdr_soft", "sdr_fpga"],
    unit: ["raw", "sfu", "kelvin"],
    output_mode: ["standard", "legacy"],
    kind: ["tracked", "fixed", "manual"],
    source: ["sun", "mercury", "venus", "mars", "jupiter", "saturn", "moon",
             "cas_a", "cyg_a", "tau_a", "vir_a", "sgr_a", "orion"],
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
        { name: "name", required: true, hint: "Any label, e.g. CALLISTO-01." },
        { name: "instrument_class", select: "instrument_class", hint: "heterodyne = e-Callisto (serial) · sdr_soft = USB SDR / RX-888 · sdr_fpga = FPGA SDR." },
        { name: "channels", type: "number", value: 200, hint: "Frequency channels per sweep (whole number, e.g. 200)." },
        { name: "sweep_rate_hz", type: "number", value: 4, hint: "Sweeps per second (e.g. 4)." },
        { name: "address", placeholder: "/dev/ttyUSB0", hint: "Serial: /dev/ttyUSB0 · USB SDR: usb:04b4:00f3 or rx888 · network: host:port · blank = simulator." },
        { name: "unit", select: "unit", hint: "raw ADC (default) · sfu / kelvin need a calibration set." },
        { name: "output_mode", select: "output_mode", hint: "standard or legacy FITS (legacy = byte-exact archive)." },
        { name: "program_id", type: "number", hint: "Frequency program ID from the Programs section (the range/channel list). Blank = 45+N MHz ramp." },
        { name: "file_seconds", type: "number", value: 900, hint: "Seconds per FITS file (e.g. 900 = 15 min)." },
        { name: "start_on_boot", type: "checkbox", hint: "Free-run: auto-record on boot and keep recording until Stop (survives reboot). Off = a manual run that does not survive a reboot." },
      ],
      actions: [
        { label: "open", href: (r) => `/portal/instruments/${r.id}` },
        { label: "record", run: (r) => api("POST", `/api/v1/instruments/${r.id}/record`) },
        { label: "stop", run: (r) => api("POST", `/api/v1/instruments/${r.id}/stop`) },
        { label: "live", href: (r) => `/portal/live/${r.id}` },
      ],
    },
    schedules: {
      title: "Schedules",
      list: "/api/v1/schedules",
      create: "/api/v1/schedules",
      del: (r) => `/api/v1/schedules/${r.id}`,
      scope: "instrument_id",
      // Blank the columns that don't apply to the row's kind so they don't
      // mislead: start/stop are fixed-mode only; source is tracked-mode only.
      cell: (c, r) => {
        if ((c === "start_utc" || c === "stop_utc") && r.kind !== "fixed") return "—";
        if (c === "source" && r.kind !== "tracked") return "—";
        return r[c] === undefined || r[c] === null ? "" : String(r[c]);
      },
      columns: ["id", "instrument_id", "kind", "source", "margin_minutes", "start_utc", "stop_utc", "program_id", "overview_at", "enabled"],
      fields: [
        { name: "instrument_id", instSelect: true, required: true, hint: "Which instrument (#id) this schedule controls." },
        { name: "kind", select: "kind", hint: "tracked = follow a source's daily ephemeris (e.g. Sun = sunrise→sunset, all year) · fixed = set times · manual = operator drives it." },
        { name: "source", select: "source", hint: "Tracked target: the window is when this source is above the horizon (Sun uses true sunrise/sunset)." },
        { name: "margin_minutes", type: "number", value: 0, hint: "Trim both ends of a tracked window by this many minutes." },
        { name: "start_utc", value: "00:00", hint: "Fixed mode start (HH:MM UTC)." },
        { name: "stop_utc", value: "23:59", hint: "Fixed mode stop (HH:MM UTC)." },
        { name: "program_id", type: "number", placeholder: "program to record (blank=ramp)" },
        { name: "overview_at", placeholder: "HH:MM scheduled overview (blank=none)" },
      ],
      actions: [
        { label: "preview", run: (r) => api("GET", `/api/v1/schedules/${r.id}/preview`), draw: drawSchedulePlan },
      ],
    },
    programs: {
      title: "Frequency programs",
      build: true,
      list: "/api/v1/programs",
      create: "/api/v1/programs",
      del: (r) => `/api/v1/programs/${r.id}`,
      columns: ["id", "name", "start_mhz", "stop_mhz", "source", "used_by"],
      fields: [
        { name: "name", required: true, hint: "Name this plan; reference its id on the instrument." },
        { name: "frequencies", json: true, placeholder: "[45.0, 55.0, 65.0]", hint: "Or paste an explicit channel list (MHz)." },
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
      columns: ["id", "name", "used_by"],
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

  // Optional per-instrument scoping (ADR-0011): when the console is mounted in
  // an instrument workspace (data-instrument set) and the resource declares a
  // `scope` query param, the list is filtered and the create form pre-fills +
  // hides that field. Absent data-instrument = today's station-wide behaviour.
  const scopeId = root.dataset.instrument || null;
  const scoped = scopeId && cfg.scope ? cfg.scope : null;
  function listUrl() {
    if (!scoped) return cfg.list;
    const sep = cfg.list.includes("?") ? "&" : "?";
    return cfg.list + sep + scoped + "=" + encodeURIComponent(scopeId);
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

  // Fold the planning plot into the schedule editor: show the tracked source's
  // elevation arc with the recording window shaded + the station horizon, so
  // you see exactly when (and why) recording happens. Fixed = window band only.
  async function drawSchedulePlan(res) {
    out.className = "muted";
    out.replaceChildren();
    const win = (res.window_start && res.window_stop)
      ? `${res.window_start.slice(11, 16)}–${res.window_stop.slice(11, 16)} UTC`
      : "no window today";
    const label = res.kind + (res.source ? ` · ${res.source}` : "") +
      ` · ${win}` + (res.recording_now ? " · recording now" : "");
    if (res.kind === "manual") { out.textContent = label + " (operator-driven)"; return; }
    const W = 520, H = 200, pad = 30;
    const cv = el("canvas", { width: String(W), height: String(H), style: "max-width:100%" });
    out.append(cv, el("div", { class: "muted", style: "margin-top:.3em" }, label));
    let track = null, horizon = 0;
    if (res.kind === "tracked") {
      try {
        const t = await api("GET", `/api/v1/planning/track?source=${res.source || "sun"}`);
        track = t.track; horizon = t.horizon_deg || 0;
      } catch (e) { /* window only */ }
    }
    const ctx = cv.getContext("2d");
    const x = (h) => pad + (h / 24) * (W - 2 * pad);
    const yEl = (e) => pad + (1 - (e + 90) / 180) * (H - 2 * pad);
    const hourOf = (iso) => { const d = new Date(iso); return d.getUTCHours() + d.getUTCMinutes() / 60; };
    ctx.clearRect(0, 0, W, H);
    if (res.window_start && res.window_stop) {
      const x0 = x(hourOf(res.window_start)), x1 = x(hourOf(res.window_stop));
      ctx.fillStyle = "rgba(90,160,255,0.18)";
      ctx.fillRect(x0, pad, Math.max(1, x1 - x0), H - 2 * pad);
    }
    ctx.strokeStyle = "rgba(255,255,255,0.12)";
    ctx.beginPath(); ctx.moveTo(x(0), yEl(0)); ctx.lineTo(x(24), yEl(0)); ctx.stroke();
    if (horizon) {
      ctx.strokeStyle = "rgba(255,200,90,0.45)";
      ctx.beginPath(); ctx.moveTo(x(0), yEl(horizon)); ctx.lineTo(x(24), yEl(horizon)); ctx.stroke();
    }
    if (track && track.length) {
      ctx.strokeStyle = "#5aa0ff"; ctx.lineWidth = 1.5; ctx.beginPath();
      track.forEach((p, i) => { const X = x(p[0]), Y = yEl(p[2]); i ? ctx.lineTo(X, Y) : ctx.moveTo(X, Y); });
      ctx.stroke();
    }
  }

  // Resolve instrument_id -> "#id name" so every config names the instrument it
  // applies to instead of showing a bare number (and badge the instruments' own
  // id as #id).
  let instMap = {};
  let countEl = null;
  function instLabel(id) {
    return instMap[id] ? "#" + id + " " + instMap[id] : "#" + id;
  }
  function renderCell(c, r) {
    if (c === "instrument_id" && r[c] != null) return instLabel(r[c]);
    if (c === "used_by") {
      const ids = r[c] || [];
      if (!ids.length) return el("span", { class: "muted" }, "unused");
      return ids.map(instLabel).join(", ");
    }
    if (root.dataset.resource === "instruments" && c === "id" && r[c] != null) {
      return "#" + r[c];
    }
    return cfg.cell ? cfg.cell(c, r) : fmt(r[c]);
  }

  async function refresh() {
    let rows;
    try { rows = await api("GET", listUrl()); } catch (e) { return note(e.message, "error"); }
    if (cfg.columns.indexOf("instrument_id") !== -1 ||
        cfg.columns.indexOf("used_by") !== -1) {
      try {
        const insts = await api("GET", "/api/v1/instruments");
        instMap = {};
        insts.forEach((i) => { instMap[i.id] = i.name; });
      } catch (e) { /* fall back to a bare #id */ }
    }
    const table = el("table");
    const thead = el("tr");
    cfg.columns.forEach((c) => thead.append(el("th", {}, c)));
    if (cfg.actions || cfg.del) thead.append(el("th", {}, ""));
    table.append(thead);
    rows.forEach((r) => {
      const tr = el("tr");
      cfg.columns.forEach((c) =>
        tr.append(el("td", {}, renderCell(c, r))));
      const td = el("td", {});
      (cfg.actions || []).forEach((a) => {
        if (a.href) {
          td.append(el("a", { href: a.href(r), style: "margin-right:.6em" }, a.label));
        } else {
          const b = el("button", { class: "btn-text", style: "margin-right:.4em;padding:.2em .6em" }, a.label);
          b.addEventListener("click", async () => {
            try {
              const res = await a.run(r);
              if (a.draw) { await a.draw(res, r); return; }
              note(a.show ? res : `${a.label}: ok`, "ok");
              refresh();
            } catch (e) { note(e.message, "error"); }
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
    if (countEl) {
      countEl.textContent = rows.length + " " + cfg.title.toLowerCase();
    }
  }

  function fmt(v) {
    if (v == null) return "";
    if (typeof v === "boolean") return v ? "yes" : "no";
    return String(v);
  }

  const body = el("div", {});
  const form = el("form", {});
  cfg.fields.forEach((f) => {
    // Scoped mount: the instrument is fixed, so hide its field and pin the value.
    if (scoped && f.name === scoped) {
      const hidden = el("input", { id: f.name, name: f.name, type: "hidden" });
      hidden.value = scopeId;
      form.append(hidden);
      return;
    }
    form.append(el("label", { for: f.name }, f.name));
    let input;
    if (f.instSelect) {
      // Pick an instrument by "#id name" instead of typing a raw id.
      input = el("select", { id: f.name, name: f.name });
      api("GET", "/api/v1/instruments").then((list) => {
        list.forEach((i) =>
          input.append(
            el("option", { value: String(i.id) }, "#" + i.id + " " + i.name)));
        if (f.value != null) input.value = String(f.value);
      }).catch(() => {});
    } else if (f.select) {
      input = el("select", { id: f.name, name: f.name });
      SELECT[f.select].forEach((o) => input.append(el("option", {}, o)));
    } else if (f.json) {
      input = el("textarea", { id: f.name, name: f.name, rows: "2", placeholder: f.placeholder || "" });
    } else if (f.type === "checkbox") {
      input = el("input", { id: f.name, name: f.name, type: "checkbox" });
      if (f.value) input.checked = true;
    } else {
      input = el("input", { id: f.name, name: f.name, type: f.type || "text" });
      if (f.value != null) input.value = f.value;
      if (f.placeholder) input.placeholder = f.placeholder;
    }
    form.append(input);
    if (f.hint) form.append(el("small", { class: "muted", style: "display:block;margin:.1em 0 .4em" }, f.hint));
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
        msg.textContent = d.count ? "pick a device to fill the form" : "none found";
      } catch (e) { msg.textContent = e.message; }
    });
    function applySelected() {
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
    }
    useBtn.addEventListener("click", applySelected);
    sel.addEventListener("change", applySelected);  // auto-fill on pick
    panel.append(btn, sel, useBtn, msg);
    return panel;
  }
  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const payload = {};
    cfg.fields.forEach((f) => {
      const elt = form.elements[f.name];
      if (f.type === "checkbox") { payload[f.name] = elt.checked; return; }
      const v = elt.value;
      if (f.json) payload[f.name] = v ? JSON.parse(v) : [];
      else if (f.type === "number" || f.instSelect) {
        if (v !== "") payload[f.name] = Number(v); // blank -> server default
      } else payload[f.name] = v;
    });
    try {
      await api("POST", cfg.create, payload);
      form.reset();
      note("created", "ok");
      refresh();
      setForm(false); // collapse back -- the new entry now shows in the list
    } catch (e) { note(e.message, "error"); }
  });

  // Programs: build a frequency list within a range (generate) or upload a frq.
  function buildPanel() {
    const wrap = el("div", { style: "margin-bottom:1rem" });
    const lbl = (t) => el("span", { class: "muted", style: "margin-right:.3em" }, t);

    const g = el("div", { class: "data-toolbar" });
    const gname = el("input", { placeholder: "name", style: "width:8em" });
    const gstart = el("input", { type: "number", value: "45", style: "width:5em", title: "start MHz" });
    const gstop = el("input", { type: "number", value: "870", style: "width:5em", title: "stop MHz" });
    const gn = el("input", { type: "number", value: "200", style: "width:5em", title: "channels" });
    const gmode = el("select", { title: "mode" });
    ["even", "quiet"].forEach((m) => gmode.append(el("option", {}, m)));
    const gbtn = el("button", { class: "btn-filled", type: "button" }, "Generate in range");
    const gmsg = el("span", { class: "muted" });
    gbtn.addEventListener("click", async () => {
      gmsg.textContent = "generating...";
      try {
        await api("POST", "/api/v1/programs/generate", {
          name: gname.value || "program",
          overview: [],
          start_mhz: Number(gstart.value),
          stop_mhz: Number(gstop.value),
          n_channels: Number(gn.value),
          mode: gmode.value,
        });
        gmsg.textContent = "created"; gname.value = ""; refresh();
      } catch (e) { gmsg.textContent = e.message; }
    });
    g.append(lbl("Generate:"), gname, lbl("from"), gstart, lbl("to"), gstop, lbl("×"), gn, gmode, gbtn, gmsg);

    const u = el("div", { class: "data-toolbar", style: "margin-top:.5em" });
    const uname = el("input", { placeholder: "name", style: "width:8em" });
    const ufile = el("input", { type: "file", accept: ".cfg,.frq,.txt" });
    const ubtn = el("button", { class: "btn-text", type: "button" }, "Upload frq file");
    const umsg = el("span", { class: "muted" });
    ubtn.addEventListener("click", async () => {
      const f = ufile.files && ufile.files[0];
      if (!f) { umsg.textContent = "pick a .cfg/.frq file"; return; }
      umsg.textContent = "importing...";
      try {
        const text = await f.text();
        await api("POST", "/api/v1/programs/import/frq", { name: uname.value || f.name, text });
        umsg.textContent = "imported"; refresh();
      } catch (e) { umsg.textContent = e.message; }
    });
    u.append(lbl("Upload frq:"), uname, ufile, ubtn, umsg);

    wrap.append(g, u, el("small", { class: "muted", style: "display:block;margin-top:.3em" },
      "Generate snaps to the 0.0625 MHz grid; 'quiet' needs an overview, else ≈ even. Or paste a list / set start-stop below."));
    return wrap;
  }

  // Layout (UX): the current setups list goes on top; the create form sits
  // below, collapsed until "New" is pressed -- a section is usually opened to
  // see and manage what exists, not to add. Card + M3 button styling to match.
  countEl = el("span", { class: "console-count muted" }, "");
  const addBtn = el("button", { class: "btn-filled", type: "button" }, "+ New");
  const listCard = el("div", { class: "card console-list" });
  listCard.append(body);
  const formCard = el("div", { class: "card console-form" });
  formCard.hidden = true;
  formCard.append(el("h3", { class: "console-form-title" }, "New entry"));
  if (cfg.scan) formCard.append(scanPanel());
  if (cfg.build) formCard.append(buildPanel());
  formCard.append(form);

  function setForm(open) {
    formCard.hidden = !open;
    addBtn.textContent = open ? "Close" : "+ New";
    if (open) {
      const first = formCard.querySelector("input, select, textarea");
      if (first) first.focus();
    }
  }
  addBtn.addEventListener("click", () => setForm(formCard.hidden));

  const toolbar = el("div", { class: "console-toolbar" });
  toolbar.append(countEl, addBtn);
  root.replaceChildren(toolbar, listCard, out, formCard);
  refresh();
  }
})();
