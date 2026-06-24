# Sprint 0.1-M4-S015 -- health checks + alerts (M4 close)

**Sprint Goal:** Show the operator the station's health -- disk, instruments,
recordings, upload backlog -- with alerts. Closes M4.

**Full ID:** 0.1-M4-S015  **Milestone:** M4 (final)  **Branch:** ``0.1-dev``  **Status:** Planned.

## Decision

Pure `compute_alerts(metrics)` + `build_report` reading disk (shutil) and DB.
System health vs data quality kept distinct (DESIGN 14); this is system health.
Clock-sync is reported tri-state (best-effort, platform-dependent) and only
alerts when known-bad.

## Deliverables (4)

| # | Task | Layer | Notes |
| -- | -- | -- | -- |
| D1 | `services/health.py` | services | HealthReport, compute_alerts (pure), build_report |
| D2 | `routes/system.py` | api | GET /api/v1/system/health + /portal/system |
| D3 | `templates/portal/system.html` + dashboard link | api | alerts + metric cards |
| D4 | tests + milestone close | tests/docs | alert logic + endpoint + page; v0.1.4, tag, push |

## Acceptance Criteria

- [ ] Alerts fire for low disk / no instruments / upload backlog / bad clock.
- [ ] Health endpoint + page render with live metrics.
- [ ] M4 tagged v0.1.4.

## Out of Scope

Reliable NTP detection; email/webhook alert delivery; auto-dispatch
(immediate/scheduled) wiring; data-quality flags (M5/refinement).
