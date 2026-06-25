# Sprint 0.4-M13-S034 -- spectrum viewer + dB toggle

**Status:** Completed (2026-06-25)  **Branch:** `0.4-dev`

## Goal / Met?
Spectrum viewer parity. **Met** -- a viewer page loads OVS/spectrum files and
applies LO conversion, dB/log, background subtraction, typed-range zoom, and PNG
export, drawn in the theme palette.

## Actions
- `services/spectrum.py` parse_two_column (comma/semicolon/space auto-detect,
  one header skipped) + list_spectra.
- `/api/v1/spectra` (list) + `/api/v1/spectra/{name}` (parsed, path-safe via
  catalog.resolve_in).
- `/portal/viewer` + `viewer.js` island (LO add/sub/rev, dB/log, subtract-min,
  X-range zoom, toDataURL PNG); Viewer nav link.

## Verification
Gate green: vulture/black/ruff/flake8/mypy (118 files)/pytest (**140 passed**).

## Lessons
- The viewer is a pure client-side transform over the parsed pairs, so LO/dB/
  background/zoom needed no backend round-trips -- only the parse is server-side.
- dB is an explicit toggle (off by default), matching the legacy XY default of
  `Digits` and DESIGN 6b.

## Tag
None (M13 closes at S035).
