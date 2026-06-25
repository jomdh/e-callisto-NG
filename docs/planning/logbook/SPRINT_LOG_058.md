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
