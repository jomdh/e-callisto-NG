# Sprint 0.7-M20-S046 -- operations cockpit

**Status:** Completed (2026-06-25)  **Branch:** `0.7-dev`

## Goal / Met?
The §8.1 read-heavy cockpit. **Met** -- the dashboard now shows a card per
instrument: recording state, current program, next scheduled action, last
upload, a live mini-waterfall, and quick actions.

## Actions
- `services/operations.py` `instrument_cockpit(db, now)` + `_next_action`
  (fixed/sun window -> "recording until HH:MM" / "next start HH:MM" / "no
  schedule").
- `GET /api/v1/operations` (instruments + disk_pct_free + clock).
- dashboard route passes the cockpit; dashboard.html cards (state chip, mini
  `cockpit-wf` canvas, meta grid, action buttons); `dashboard.js` (per-card WS
  mini-waterfall, quick actions, 10s refresh); cockpit CSS grid.

## Verification
Gate green: vulture/black/ruff/flake8/mypy (139 files)/pytest (**184 passed**).

## Lessons
- The mini-waterfall reuses the same WS hub + 8-bit colormap as the full live
  view -- one frame format, two surfaces.

## Tag
None (M20 closes at S047).
