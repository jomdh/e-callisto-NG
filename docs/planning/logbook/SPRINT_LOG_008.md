# Sprint 0.1-M1-S008 -- portal shell: M3 design system + login + dashboard

**Status:** Completed (2026-06-25)  **Branch:** ``0.1-dev``

## Goal / Met?

A themed, server-rendered web entry point. **Met** -- the login page renders on
the M3 design system; form login lands on the dashboard; anonymous `/portal`
redirects to login.

## Actions Taken

- **D1 CSS.** `static/css/material-design-system.css` -- compact M3 tokens with
  Nebula (dark, default) / Supernova (light), shared visual language with
  doncel; `portal.css` layout; `static/js/portal.js` (theme toggle via
  `addEventListener` + `data-action`, no inline handlers).
- **D2 templates.** `templates/portal/{base,login,dashboard}.html`; base does the
  pre-render theme bootstrap.
- **D3 wiring.** `api/templating.py` (Jinja2Templates + static dir); StaticFiles
  mount; `auth.optional_user` (non-raising lookup for pages).
- **D4 `api/routes/portal.py`.** GET / (login or redirect), POST /login (form),
  GET /logout, GET /portal (dashboard with instruments + station).
- **D5 tests.** Login renders, form login -> dashboard, bad login -> 401 error,
  anon redirect, static CSS served. Added `python-multipart` (forms) +
  package-data so templates/static ship in builds.

## Verification

Gate green: vulture/black/ruff/flake8/mypy (48 files)/pytest (**41 passed**).

## Lessons

- FastAPI form routes need `python-multipart`; caught immediately by the test.
- Server-side form login keeps the basic flow JS-free; the only JS island so far
  is the theme toggle. CSP middleware is a later hardening sprint.

## Tag

None (M1 closes at S009 with the wizard).
