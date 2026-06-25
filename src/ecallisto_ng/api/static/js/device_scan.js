// Wizard instrument step: scan for hardware and fill the instrument fields.
// CSP-safe external file; no-op unless the scan controls are on the page.
(function () {
  "use strict";
  const btn = document.getElementById("scan-btn");
  const sel = document.getElementById("scan-pick");
  const use = document.getElementById("scan-use");
  const msg = document.getElementById("scan-msg");
  if (!btn || !sel || !use) return;

  let devices = [];

  async function scan() {
    msg.textContent = "scanning + probing...";
    try {
      const r = await fetch("/api/v1/discovery/scan?probe=true");
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || r.status);
      devices = d.devices || [];
      sel.replaceChildren();
      const head = document.createElement("option");
      head.value = "";
      head.textContent = `-- ${d.count} device(s) --`;
      sel.append(head);
      devices.forEach((dev, i) => {
        const o = document.createElement("option");
        o.value = String(i);
        o.textContent =
          `${dev.address} - ${dev.detail || dev.description} ` +
          `[${dev.suggested_class}]`;
        sel.append(o);
      });
      msg.textContent = d.count
        ? "pick a device, then 'use selected'"
        : "none found";
    } catch (e) {
      msg.textContent = e.message;
    }
  }

  function applySelected() {
    if (sel.value === "") return;
    const dev = devices[Number(sel.value)];
    if (!dev) return;
    const cls = document.getElementById("instrument_class");
    const addr = document.getElementById("address");
    const name = document.getElementById("instrument_name");
    if (cls) cls.value = dev.suggested_class;
    // keep the address for serial (/dev/tty...) and USB (usb:vid:pid) alike so
    // the driver can route (e.g. an RX-888 by its USB id).
    if (addr) addr.value = dev.address;
    if (name && !name.value) {
      name.value = dev.kind === "serial" ? "Callisto" : "SDR";
    }
    msg.textContent = `filled from ${dev.address}`;
  }

  btn.addEventListener("click", scan);
  use.addEventListener("click", applySelected);
})();
