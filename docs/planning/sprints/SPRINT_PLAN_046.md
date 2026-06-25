# Sprint 0.7-M20-S046 -- operations cockpit

**Goal:** A live per-instrument dashboard cockpit (DESIGN 8.1).
**Full ID:** 0.7-M20-S046  **Milestone:** M20  **Branch:** `0.7-dev`  **Status:** Completed.

## Deliverables
- `services/operations.instrument_cockpit` (state, last file, next scheduled
  action, last upload, program) + `_next_action` (sun/fixed window).
- `GET /api/v1/operations` (cockpit + disk/clock).
- Dashboard: per-instrument cards with state chip, **mini-waterfall** (WS), quick
  record/stop/overview/live + 10s status refresh; cockpit CSS.

## Acceptance
- [x] Cockpit fields + next-action correct; endpoint + dashboard cards render.
- [x] Gate green; 184 tests.
