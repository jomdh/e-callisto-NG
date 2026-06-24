# Sprint 0.1-M1-S008 -- portal shell: M3 design system + login + dashboard

**Sprint Goal:** Give the operator a themed, server-rendered web entry point --
log in and see the station dashboard.

**Full ID:** 0.1-M1-S008  **Milestone:** M1  **Branch:** ``0.1-dev``  **Status:** Planned.

## Decision

Server-rendered Jinja portal (ADR-0001) on a compact, framework-agnostic **M3
design system** (Nebula/Supernova themes) -- the coherence asset shared with
doncel, trimmed to what the station portal needs. Login is a server-side form
(no JS required) that reuses the auth service; the dashboard lists instruments
and shows health.

## Deliverables (5)

| # | Task | Layer | Notes |
| -- | -- | -- | -- |
| D1 | `static/css/material-design-system.css` + `portal.css` | api | M3 tokens, Nebula (dark) / Supernova (light), base components |
| D2 | `templates/portal/{base,login,dashboard}.html` | api | base theme bootstrap; login form; dashboard |
| D3 | templates/static wiring + `optional_user` helper | api | Jinja2Templates, StaticFiles mount, non-raising user lookup |
| D4 | `api/routes/portal.py` | api | GET / (login/redirect), POST /login (form), GET /logout, GET /portal |
| D5 | tests + logbook | tests | login page renders; form login -> dashboard; anon /portal redirects |

## Acceptance Criteria

- [ ] GET / serves the themed login page.
- [ ] Form login with valid creds redirects to /portal (dashboard, 200).
- [ ] GET /portal while anonymous redirects to /.
- [ ] Theme tokens drive colors; default theme Nebula.
- [ ] Gate green; tests pass.

## Out of Scope

Install wizard (S009), live waterfall (M2), per-instrument control UI beyond a
listing.
