# Sprint 0.7-M23-S051 -- astro source-track planning panel

**Goal:** Source az/el-vs-horizon planning panel (legacy `astro`, F8).
**Full ID:** 0.7-M23-S051  **Milestone:** M23  **Branch:** `0.7-dev`  **Status:** Completed.

## Deliverables
- `services/astro_track.source_track` (astropy: Sun/planets/Moon/fixed radio
  sources -> (ut_hour, az, el)).
- `Station.horizon_deg`; `GET /api/v1/planning/track`.
- Planning page + planning.js (canvas: elevation track + horizon lines); nav.

## Acceptance
- [x] Sun culminates >40 deg at solstice; fixed sources; endpoint + page render.
- [x] Gate green; 209 tests.
