# Sprint 0.7-M20-S047 -- data browser depth (M20 close)

**Goal:** Calendar heatmap + in-browser FITS viewer + bulk ops. Closes M20.
**Full ID:** 0.7-M20-S047  **Milestone:** M20 (final)  **Branch:** `0.7-dev`  **Status:** Completed.

## Deliverables
- `catalog.recordings_by_day` (filename date) + `catalog.fits_header`.
- `GET /api/v1/files/calendar`, `/{name}/header`; `POST /files/bulk/delete`,
  `/files/bulk/requeue`.
- data.html + data.js: 8-week heatmap, select-all + bulk delete/re-queue,
  click-to-view FITS (quicklook + header dialog); CSS.

## Acceptance
- [x] Calendar counts per day; header parsed; bulk delete/requeue work.
- [x] Data page renders heatmap + bulk + viewer. Gate green; M20 -> v0.7.0.
