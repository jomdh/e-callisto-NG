// Time page: poll the active time source. CSP-safe external file.
(function () {
  "use strict";
  function set(id, v) {
    const el = document.getElementById(id);
    if (el) el.textContent = v;
  }
  function refresh() {
    fetch("/api/v1/system/time")
      .then((r) => r.json())
      .then((d) => {
        set("t-source", d.source);
        set("t-lock", d.locked ? "locked" : "unlocked");
        set("t-offset", d.offset_ms == null ? "unknown" : d.offset_ms + " ms");
        set("t-now", d.now);
      })
      .catch(() => {});
  }
  refresh();
  setInterval(refresh, 5000);
})();
