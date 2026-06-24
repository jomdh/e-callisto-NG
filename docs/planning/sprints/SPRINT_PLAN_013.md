# Sprint 0.1-M3-S013 -- sun-relative scheduler (M3 close)

**Sprint Goal:** Schedule recordings to follow the Sun for the station's
coordinates. Closes M3.

**Full ID:** 0.1-M3-S013  **Milestone:** M3 (final)  **Branch:** ``0.1-dev``  **Status:** Planned.

## Decision

astropy computes sunrise/transit/sunset by sampling solar altitude across the day
and finding zero-crossings -- accurate, dependency-light, no Emacs (DESIGN 12).
The window decision is a pure function; a `Schedule` row + preview endpoint expose
it. The live time-driven trigger loop is a thin layer over the pure logic.

## Deliverables (5)

| # | Task | Layer | Notes |
| -- | -- | -- | -- |
| D1 | `services/scheduler.py` | services | `sun_events`, `sun_window`, `is_recording_desired` |
| D2 | `Schedule` model | api | per-instrument; sun/fixed; margin |
| D3 | `routes/schedules.py` CRUD + preview | api | today's window + recording_now |
| D4 | tests | tests | ephemeris sanity (equator/equinox) + window + API |
| D5 | milestone close | docs | v0.1.3, changelog, ROADMAP, tag, push |

## Acceptance Criteria

- [ ] Sun events sane: equator equinox rise~06h/transit~12h/set~18h UTC.
- [ ] Window + `is_recording_desired` correct at noon vs midnight.
- [ ] Schedule CRUD + preview; M3 tagged v0.1.3.

## Out of Scope

The background trigger thread wiring to the recorder (refinement); transit-restart
and overnight-overview entries; fixed-mode window computation.
