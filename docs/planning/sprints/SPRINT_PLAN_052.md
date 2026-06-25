# Sprint 0.7-M23-S052 -- offline map picker (M23 close)

**Goal:** CSP-safe offline coordinate map picker in the wizard (F16). Closes M23.
**Full ID:** 0.7-M23-S052  **Milestone:** M23 (final)  **Branch:** `0.7-dev`  **Status:** Completed.

## Deliverables
- `mappicker.js`: equirectangular graticule + draggable marker, two-way synced to
  lat/lon inputs (no CDN/tiles).
- Wizard coordinates step: map canvas + script.

## Acceptance
- [x] Coordinates step shows the map + syncs the wizard's lat/lon inputs.
- [x] Gate green; M23 -> v0.7.3.

## Note
Continents outline (vs the graticule) -> future cosmetic polish (still offline).
