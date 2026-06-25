# Sprint 0.7-M20-S047 -- data browser depth (M20 close)

**Status:** Completed (2026-06-25)  **Branch:** `0.7-dev`

## Goal / Met?
Richer data browsing (F13). **Met** -- an 8-week activity heatmap, multi-select
with bulk delete / re-queue, and an in-browser FITS viewer (quicklook image +
header cards).

## Actions
- `catalog.recordings_by_day` (counts per YYYY-MM-DD from the filename date) +
  `catalog.fits_header` (selected primary cards).
- Endpoints: `/files/calendar`, `/files/{name}/header`, `POST /files/bulk/delete`
  (file + its upload jobs), `POST /files/bulk/requeue` (drop done jobs).
- data.html + data.js: heatmap render, select-all/per-file checkboxes, bulk
  actions with confirm, FITS viewer `<dialog>` (quicklook + header table); CSS.

## Verification
Gate green: vulture/black/ruff/flake8/mypy (140 files)/pytest (**189 passed**).

## Milestone M20 -- complete
S046-S047. The operations cockpit (live per-instrument cards + mini-waterfalls +
quick actions) and the data-browser depth (heatmap + FITS viewer + bulk ops).
Version -> v0.7.0; tag.

## Lessons
- Re-queue = "drop the done upload jobs" -- the uploader's idempotent
  upload-pending then re-sends on its next tick. No new upload code needed.

## Tag
`v0.7.0` at the M20-complete commit on `0.7-dev`.
