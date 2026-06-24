# Sprint 0.1-M1-S009 -- install wizard (M1 close)

**Status:** Completed (2026-06-25)  **Branch:** ``0.1-dev``

## Goal / Met?

Set up a fresh station entirely in the browser. **Met** -- first-run gate routes
to `/wizard`, which creates the admin + station + instrument and logs the admin
in. M1 complete.

## Actions Taken

- **D1 `api/setup.py`** `is_configured` (true once any user exists).
- **D2 `routes/wizard.py`** GET/POST `/wizard`: create admin (ADMIN role),
  upsert the single Station row with coordinates, optional first Instrument,
  auto-login; guarded so it no-ops once configured.
- **D3 gate** in `portal.index`: unconfigured -> `/wizard`.
- **D4 `templates/portal/wizard.html`** -- admin + station + instrument form on
  the M3 design system.
- **D5 tests** -- fresh-install redirect, full wizard -> dashboard (admin logged
  in, station + instrument shown), re-run blocked. Adjusted the login-page test
  to seed a user (the gate now intercepts unconfigured `/`).

## Verification

Gate green: vulture/black/ruff/flake8/mypy (51 files)/pytest (**44 passed**).

## Milestone M1 -- complete

S005-S009 logged Completed. An operator can run the wizard, log in, register an
instrument, and start/stop a recording from the browser. Version -> v0.1.1;
changelog; tag `v0.1.1`; branch pushed. The full multi-step wizard (time sync,
access mode, schedule, upload targets) is deferred to refinement sprints; the
essential setup + the three core records are in place.

## Lessons

- The first-run gate is a cross-cutting redirect; one existing test assumed `/`
  always shows login. Cheap fix, but a reminder that gates change baseline
  routing for every page test.

## Tag

``v0.1.1`` at the M1-complete commit on ``0.1-dev``.
