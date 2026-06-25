# Sprint 0.4-M13-S034 -- spectrum viewer + dB toggle

**Goal:** Interactive 2-column spectrum viewer (legacy M9703APlotter) with LO
conversion, dB/log, background subtraction, typed-range zoom, PNG export.
**Full ID:** 0.4-M13-S034  **Milestone:** M13  **Branch:** `0.4-dev`  **Status:** Completed.

## Deliverables
- `services/spectrum.py` (parse_two_column delimiter auto-detect; list_spectra).
- `GET /api/v1/spectra` + `GET /api/v1/spectra/{name}` (path-safe).
- `/portal/viewer` + `viewer.js` (LO modes, dB/log + subtract-min toggles, typed
  X-range zoom, canvas PNG export) -- theme-coloured; nav link.

## Acceptance
- [x] Parses comma/semicolon/space, skips header; lists spectrum files.
- [x] Endpoints return parsed freqs/amps; viewer page renders. Gate green.
