# Sprint 0.1-M1-S009 -- install wizard (M1 close)

**Sprint Goal:** A fresh station can be set up entirely in the browser -- create
the admin, name the station, add an instrument -- with no terminal. Closes M1.

**Full ID:** 0.1-M1-S009  **Milestone:** M1 (final)  **Branch:** ``0.1-dev``  **Status:** Planned.

## Decision

First-run gate: until at least one user exists, every page routes to `/wizard`.
The wizard is a single server-side form (MVP of the 10-step flow in DESIGN 9)
that creates the **admin** (no default credentials), the **station** identity +
coordinates, and an optional first **instrument**, then logs the admin in. The
multi-step elaboration is deferred; the gate + the three essential records are
what M1 needs.

## Deliverables (5)

| # | Task | Layer | Notes |
| -- | -- | -- | -- |
| D1 | `api/setup.py` `is_configured` | api | true once any user exists |
| D2 | `routes/wizard.py` GET/POST `/wizard` | api | create admin+station+instrument; auto-login; guard if configured |
| D3 | first-run gate in portal index | api | unconfigured -> /wizard |
| D4 | `templates/portal/wizard.html` | api | admin + station + instrument form, M3-styled |
| D5 | tests + milestone close | tests/docs | wizard flow; v0.1.1 bump, changelog, ROADMAP, tag, push |

## Acceptance Criteria

- [ ] Fresh install: GET / redirects to /wizard; wizard renders.
- [ ] POST /wizard creates admin+station+instrument, logs in, lands on dashboard.
- [ ] After setup, /wizard redirects away (no re-setup).
- [ ] No default credentials anywhere.
- [ ] Gate green; M1 tagged v0.1.1.

## Out of Scope

The full multi-step wizard (time sync, access mode, schedule, upload targets) --
later M-sprints / refinement; live waterfall (M2).
