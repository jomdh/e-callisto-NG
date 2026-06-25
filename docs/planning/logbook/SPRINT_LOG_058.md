# Sprint 0.8-S058 -- hardware discovery (Callisto / SDR scan)

**Status:** Completed (2026-06-25)  **Branch:** `0.8-dev`
**Driver:** operator request -- test a remote Pi's PL2303 serial link + classify
attached SDRs (RX-888 MkII = Cypress FX3) from the portal.

## Actions
- `services/discovery.py`: `scan_serial_ports(probe)` (pyserial comports +
  optional Callisto handshake), `scan_usb_devices()` (Linux /sys vs a known-SDR
  VID:PID table), `probe_callisto()` (open + `S0`/`?` -> `$CRX` check),
  `discover()` -> DiscoveredDevice list with suggested_class + address. Degrades
  to empty where the OS lacks the interface; never raises.
- `GET /api/v1/discovery/scan?probe=` (operator).
- `/portal/hardware` page + hardware.js (scan / scan+probe, create-instrument
  from a found device) + Hardware nav link.
- `scripts/scan_devices.py`: standalone, pyserial-only, pullable on the station
  (`--probe`, `--port`) -- confirms the serial->Callisto link without the suite.

## Verification
+test_discovery (7: as_dict hex, graceful bad-port probe, endpoint, RBAC,
known-SDR table, page). Gate green: **239 passed**.

## Notes
- Known SDRs: RX-888 MkII (04b4:00f3 FX3 DFU + 00f1), RTL-SDR, Airspy, HackRF,
  SDRplay. Serial bridges (PL2303/FTDI/CP2102) are Callisto candidates, probed
  to confirm.

---

# Sprint 0.8-S059 -- wire device scan into Add Instrument + wizard

**Status:** Completed (2026-06-25)  **Branch:** `0.8-dev`
**Driver:** operator -- selecting a specific device when a station has several.

## Actions
- console.js: `scan: true` on the instruments resource -> a scan panel above the
  Add Instrument form (Scan + probe -> a `<select>` of detected devices, each
  labelled by **address** so multiple devices are individually selectable;
  "use selected" fills name/class/address).
- Wizard instrument step: same scan widget + a new **address** field; device_scan.js
  island; wizard persists `address` (carried through steps generically).
- The address uniquely identifies each device (/dev/ttyUSB0 vs ttyUSB1).

## Verification
+test_scan_wiring (4: console scan opt-in, wizard step controls+address, wizard
persists the chosen /dev/ttyUSB0, asset served). Gate green: **243 passed**.
Live: console.js carries scan, device_scan.js 200, pages 200.
