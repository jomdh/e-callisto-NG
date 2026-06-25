# Sprint 0.7-M23-S052 -- offline map picker (M23 close)

**Status:** Completed (2026-06-25)  **Branch:** `0.7-dev`

## Goal / Met?
Offline map picker (F16). **Met** -- the wizard coordinates step has a clickable/
draggable equirectangular map that sets lat/lon, two-way synced with the numeric
inputs, with no external tiles (CSP-safe).

## Actions
- `static/js/mappicker.js`: canvas equirectangular graticule (30 deg grid +
  equator/prime-meridian), draggable crosshair marker, click/drag -> lat/lon,
  numeric inputs <-> marker both ways.
- Wizard coordinates step: `#map-canvas` + script load.

## Verification
Gate green: vulture/black/ruff/flake8/mypy (150 files)/pytest (**211 passed**).

## Milestone M23 -- complete
S051-S052. Planning aids: the astro source-track panel + the offline map picker.
Version -> v0.7.3; tag.

## Lessons
- A canvas graticule + linear equirectangular math is a fully offline, CSP-safe
  picker -- the continents outline is cosmetic and can come later without a CDN.

## Tag
`v0.7.3` at the M23-complete commit on `0.7-dev`.
