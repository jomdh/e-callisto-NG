# Sprint 0.1-M2-S011 -- data browser + quicklooks + download (M2 close)

**Status:** Completed (2026-06-25)  **Branch:** ``0.1-dev``

## Goal / Met?

Browse, preview, and download recorded files in the portal. **Met** -- a recorded
FITS is listed, downloadable, and rendered as a PNG quicklook; traversal is
rejected.

## Actions Taken

- **D1 `services/catalog.py`** -- `list_recordings` (glob + FITS header read),
  `resolve_in` (path-traversal-safe basename resolution), `quicklook_png` (lazy
  Pillow grayscale PNG, cached).
- **D2 `routes/data.py`** -- GET /api/v1/files, /files/{name}/download (FileResponse,
  FITS), /files/{name}/quicklook (PNG); viewer role.
- **D3/D4** `GET /portal/data` + `templates/portal/data.html` (quicklook cards +
  download), dashboard links to data + per-instrument live.
- **D5 tests** -- list/download/quicklook round-trip (FITS magic + PNG magic),
  traversal rejected (404), data page renders. Added `pillow` dep.

## Verification

Gate green: vulture/black/ruff/flake8/mypy (57 files)/pytest (**50 passed**).

## Milestone M2 -- complete

S010-S011 logged. Operators watch a live waterfall and browse/download files.
Version -> v0.1.2; changelog; tag `v0.1.2`; pushed. Scan-based catalog (no DB
table) keeps `services` free of an `api` dependency and avoids index drift.

## Lessons

- A scan-based catalog trades a little per-list IO for zero index-drift risk --
  the right call at station data volumes; revisit with a cache if a station
  accumulates very many files.

## Tag

``v0.1.2`` at the M2-complete commit on ``0.1-dev``.
