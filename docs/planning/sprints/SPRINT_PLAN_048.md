# Sprint 0.7-M21-S048 -- DB-backed recorder run-state (cross-process)

**Goal:** The web app reflects acquisition state even when the `acquire` daemon
owns the loops (ADR-0007 / F14).
**Full ID:** 0.7-M21-S048  **Milestone:** M21  **Branch:** `0.7-dev`  **Status:** Completed.

## Deliverables
- `RecorderRuntime` model; `services/recorder_state` write/read.
- `recorder.start` gains an `on_state(state, last_file)` callback (recorder stays
  api-free); record route + scheduler persist via it.
- `operations.instrument_cockpit` reads the persisted runtime (fallback in-memory).

## Acceptance
- [x] State persists on start/finish; cockpit shows a DB-only ("other process")
      recording. Gate green; 192 tests.
