# Sprint 0.4-M13-S035 -- public light-curve PNG + live panels (M13 close)

**Goal:** wwwgeni-style 24-h UT light-curve PNG + live y(f)/y(t) panels + dB.
**Full ID:** 0.4-M13-S035  **Milestone:** M13 (final)  **Branch:** `0.4-dev`  **Status:** Completed.

## Deliverables
- `services/lightcurve_png.py` (Pillow): 800x496, 24-h UT axis, <=10 colored
  channel traces from a daily LC file.
- `GET /api/v1/lightcurves` + `/api/v1/lightcurves/{name}/png`.
- Live page: single-spectrum y(f) + light-curve y(t) panels + dB toggle.

## Acceptance
- [x] PNG renders at 800x496 from an LC file; endpoints serve it.
- [x] Live page shows spectrum + LC panels + dB toggle. Gate green; v0.4.2.
