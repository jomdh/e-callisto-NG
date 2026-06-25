# Sprint 0.8-M25-S054 -- per-instrument device console

**Goal:** Device functions inside each instrument's entry, class-gated.
**Full ID:** 0.8-M25-S054  **Milestone:** M25 (final)  **Branch:** `0.8-dev`  **Status:** Completed.

## Deliverables
- `GET /api/v1/instruments/{id}/capabilities` (bench/overview/class).
- `/portal/instruments/{id}` detail page: operate actions (record/stop/overview/
  diagnose/reconnect/live) + class-gated bench detector + NF (heterodyne only) +
  configure links; instrument.js island.
- console "open" action + dashboard card name link to the detail page.

## Acceptance
- [x] Heterodyne detail shows bench/NF/reconnect; SDR hides them; capabilities
      endpoint correct. Gate green; M25 -> v0.8.0.
