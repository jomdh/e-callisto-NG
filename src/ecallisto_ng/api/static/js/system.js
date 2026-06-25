// System page: host actions (via hook) + log tail. CSP-safe external file.
(function () {
  "use strict";

  async function post(url) {
    const r = await fetch(url, { method: "POST" });
    const t = await r.text();
    try { return JSON.parse(t); } catch (e) { return { message: t }; }
  }

  const msg = document.getElementById("host-msg");
  function wire(id, url, confirmText) {
    const b = document.getElementById(id);
    if (!b) return;
    b.addEventListener("click", async () => {
      if (confirmText && !window.confirm(confirmText)) return;
      msg.textContent = "...";
      const res = await post(url);
      msg.textContent = res.message || (res.ok ? "ok" : "failed");
    });
  }
  wire("host-update", "/api/v1/system/update/apply");
  wire("host-rollback", "/api/v1/system/update/rollback");
  wire("host-reboot", "/api/v1/system/reboot", "Reboot the station now?");
  wire("host-shutdown", "/api/v1/system/shutdown", "Shut down the station?");

  const log = document.getElementById("host-log");
  if (log) {
    fetch("/api/v1/system/log?lines=200")
      .then((r) => r.json())
      .then((d) => { log.textContent = (d.lines || []).join(""); })
      .catch((e) => { log.textContent = String(e); });
  }
})();
