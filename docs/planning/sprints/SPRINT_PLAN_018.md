# Sprint 0.2-M6-S018 -- scheduler drives recording

**Sprint Goal:** A station records on its schedule with no operator action --
start/stop driven by the sun (or fixed) window.

**Full ID:** 0.2-M6-S018  **Milestone:** M6  **Branch:** ``0.2-dev``  **Status:** Planned.

## Decision

A `SchedulerService` background loop ticks every N seconds: for each enabled
schedule it computes today's window (sun via station coords, or fixed times) and
starts/stops the instrument's recorder accordingly. File-period rollover falls
out naturally -- when a bounded recording finishes and the window still holds,
the next tick re-arms it. `tick(now)` is the testable unit; the thread just calls
it. Disabled in tests via a 0 tick interval.

## Deliverables (5)

| # | Task | Layer | Notes |
| -- | -- | -- | -- |
| D1 | `Instrument.file_seconds`; `scheduler.fixed_window` | api/services | per-file length; fixed-mode window |
| D2 | `services/scheduler_service.py` `SchedulerService.tick` | services | desired window -> start/stop recorder |
| D3 | background loop + settings `scheduler_tick_seconds` | services/api | started in lifespan; 0 = off (tests) |
| D4 | wire into app lifespan; conftest sets tick=0 | api/tests | -- |
| D5 | tests + logbook | tests | tick at noon records a file; at midnight does not |

## Acceptance Criteria

- [ ] tick within the sun window starts a recording (file lands); outside it does not.
- [ ] tick stops a recording when the window closes.
- [ ] Scheduler loop is off in tests (deterministic).
- [ ] Gate green; SNR clean.

## Out of Scope

Auto-dispatch uploads + retention (S019); calibration wiring + light curves (S020).
