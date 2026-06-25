# Sprint 0.5-M16-S041 -- acquisition process isolation + drift-gating (M16 close)

**Goal:** Acquisition runnable as its own supervised process + finer drift-gating.
**Full ID:** 0.5-M16-S041  **Milestone:** M16 (final)  **Branch:** `0.5-dev`  **Status:** Completed.

## Deliverables
- ADR-0007; `run_loops_in_web` setting + lifespan guard; CLI `ecallisto-ng
  acquire` daemon; `ecallisto-acquire.service` unit.
- `clock.within_drift` + `clock_offset_ms` (chronyc); `max_clock_offset_ms`
  setting; scheduler gate uses it.

## Acceptance
- [x] `acquire` subcommand + unit packaged; web loop guarded by the setting.
- [x] Drift gate blocks beyond tolerance, allows unknown/off. Gate green; v0.5.1.

## Deferred
DB-backed cross-process recorder status -> F14 (ADR-0007 known limitation).
