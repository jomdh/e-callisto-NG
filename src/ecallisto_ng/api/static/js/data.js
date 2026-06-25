// Data browser depth: calendar heatmap, selection + bulk ops, in-browser FITS
// viewer (quicklook + header). CSP-safe external file.
(function () {
  "use strict";

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

  // ---- calendar heatmap (last 56 days) ----
  const cal = document.getElementById("cal-heatmap");
  if (cal) {
    api("GET", "/api/v1/files/calendar").then((counts) => {
      const max = Math.max(1, ...Object.values(counts));
      const cells = [];
      const today = new Date();
      for (let i = 55; i >= 0; i--) {
        const d = new Date(today);
        d.setDate(today.getDate() - i);
        const key = d.toISOString().slice(0, 10);
        const n = counts[key] || 0;
        const lvl = n === 0 ? 0 : Math.ceil((n / max) * 3);
        const cell = document.createElement("span");
        cell.className = "cal-cell cal-l" + lvl;
        cell.title = key + ": " + n + " file(s)";
        cells.push(cell);
      }
      cal.replaceChildren(...cells);
    }).catch((e) => { cal.textContent = e.message; });
  }

  // ---- selection + bulk ----
  const checks = () => Array.from(document.querySelectorAll(".file-check"));
  const selected = () => checks().filter((c) => c.checked).map((c) => c.value);
  const count = document.getElementById("sel-count");
  function updateCount() {
    if (count) count.textContent = selected().length + " selected";
  }
  checks().forEach((c) => c.addEventListener("change", updateCount));
  const all = document.getElementById("sel-all");
  if (all) {
    all.addEventListener("change", () => {
      checks().forEach((c) => { c.checked = all.checked; });
      updateCount();
    });
  }

  const msg = document.getElementById("bulk-msg");
  async function bulk(url, confirmText) {
    const names = selected();
    if (!names.length) { msg.textContent = "nothing selected"; return; }
    if (confirmText && !window.confirm(confirmText + names.length + " file(s)?"))
      return;
    try {
      const res = await api("POST", url, { names });
      msg.textContent = JSON.stringify(res);
      if (url.endsWith("/delete")) {
        names.forEach((n) => {
          const card = document.querySelector(`.card[data-name="${n}"]`);
          if (card) card.remove();
        });
      }
      updateCount();
    } catch (e) { msg.textContent = e.message; }
  }
  const del = document.getElementById("bulk-delete");
  if (del) del.addEventListener("click", () =>
    bulk("/api/v1/files/bulk/delete", "Delete "));
  const rq = document.getElementById("bulk-requeue");
  if (rq) rq.addEventListener("click", () =>
    bulk("/api/v1/files/bulk/requeue", null));

  // ---- in-browser FITS viewer ----
  const dlg = document.getElementById("fits-viewer");
  function openViewer(name) {
    document.getElementById("fv-name").textContent = name;
    document.getElementById("fv-img").src =
      `/api/v1/files/${encodeURIComponent(name)}/quicklook`;
    const tbl = document.getElementById("fv-header");
    tbl.replaceChildren();
    api("GET", `/api/v1/files/${encodeURIComponent(name)}/header`)
      .then((h) => {
        Object.entries(h).forEach(([k, v]) => {
          const tr = document.createElement("tr");
          const tk = document.createElement("td");
          tk.textContent = k;
          const tv = document.createElement("td");
          tv.textContent = v;
          tr.append(tk, tv);
          tbl.append(tr);
        });
      })
      .catch(() => {});
    if (dlg.showModal) dlg.showModal();
  }
  document.querySelectorAll(".file-view, .file-thumb").forEach((el) =>
    el.addEventListener("click", () => openViewer(el.dataset.name))
  );
  const close = document.getElementById("fv-close");
  if (close) close.addEventListener("click", () => dlg.close());
})();
