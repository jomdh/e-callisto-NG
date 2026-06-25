# Sprint 0.4-M13-S035 -- public light-curve PNG + live panels (M13 close)

**Status:** Completed (2026-06-25)  **Branch:** `0.4-dev`

## Goal / Met?
Public LC PNG + live panels. **Met** -- a Pillow renderer turns a daily LC file
into the legacy 24-h UT light-curve image; the live view gains single-spectrum
and light-curve panels plus a dB toggle.

## Actions
- `services/lightcurve_png.py` render_lightcurve_png (800x496, 24-h UT ticks,
  <=10 distinct-colour traces, frequency legend).
- `/api/v1/lightcurves` (list) + `/api/v1/lightcurves/{name}/png` (render+serve).
- live.html + waterfall.js: spectrum y(f) + light-curve y(t) panels (peak
  channel), dB toggle (raw 0-255 / 10log10), theme-accent traces.

## Verification
Gate green: vulture/black/ruff/flake8/mypy (120 files)/pytest (**143 passed**).

## Milestone M13 -- complete
S034-S035. The visualization + publication parity: an interactive spectrum
viewer (LO/dB/background/zoom/PNG), the dB toggle across live + viewer, the
public light-curve PNG, and the three legacy live plots (waterfall + y(f) +
y(t)). Version -> v0.4.2; tag v0.4.2.

## Lessons
- The published PNG is a *data product*, so it uses a fixed distinct palette;
  the UI chrome stays on theme tokens -- the colour policy applies to chrome, not
  to scientific image content.

## Tag
`v0.4.2` at the M13-complete commit on `0.4-dev`.
