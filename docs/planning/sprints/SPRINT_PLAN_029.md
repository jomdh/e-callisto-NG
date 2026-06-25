# Sprint 0.3-MUI-S029 -- portal UI for operator features

**Sprint Goal:** Make every backend feature reachable from the browser, not just
the API docs.

**Full ID:** 0.3-MUI-S029  **Milestone:** MUI (usability)  **Branch:** ``0.2-dev``  **Status:** Planned.

## Problem

v0.1-v0.3 shipped the backends (schedules, programs, calibration, uploads,
access, import, fleet, instrument actions) but the portal only surfaced login,
dashboard, live, data, and system. The rest was API-only.

## Decision

The API already authenticates via the **session cookie**, so portal JS islands
can `fetch()` the existing endpoints directly (CSP-safe: external scripts,
same-origin). A single **config-driven console** (`console.js`) renders a
list + create form + row actions for each resource; dedicated pages cover the
form-shaped settings (access, import, fleet).

## Deliverables (5)

| # | Task | Layer | Notes |
| -- | -- | -- | -- |
| D1 | shared nav partial + nav CSS; dashboard uses it | templates | links to every section |
| D2 | `console.js` generic CRUD island + `/portal/manage/{resource}` | static/api | instruments/schedules/programs/calibration/uploads/peers |
| D3 | `settings.js` + access/import/fleet pages + routes | static/api/templates | load+save / textareas / aggregate |
| D4 | instrument row actions (record/stop/diagnose/live) | static | via existing endpoints |
| D5 | tests + ship | tests/docs | pages render + login-gated; v0.3.2 |

## Acceptance Criteria

- [ ] Every backend feature has a clickable page reachable from the nav.
- [ ] Pages are login-gated (anon -> redirect to /).
- [ ] No inline scripts (CSP holds).
- [ ] Gate green; SNR clean.

## Out of Scope

Inline editing/PATCH of rows; pagination; per-field validation UX; wizard
expansion. (Refinements.)
