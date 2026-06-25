# Sprint 0.3-MUI-S029 -- portal UI for operator features

**Status:** Completed (2026-06-25)  **Branch:** ``0.2-dev`` -> merged to ``main``

## Goal / Met?

Make every backend feature reachable from the browser. **Met** -- a shared nav,
a config-driven CRUD console covering six resources, and dedicated access/import/
fleet pages. Everything that was API-only is now clickable.

## Trigger

Operator feedback: "most features are unreachable" -- the portal had grown only
to login/dashboard/live/data/system while v0.2-v0.3 added many API-only backends.

## Actions Taken

- **D1** `templates/portal/_nav.html` + nav CSS; dashboard switched to the nav and
  gained a "Manage instruments" entry point.
- **D2** `static/js/console.js` -- generic CRUD island (list + create form + row
  actions + delete), config per resource; `/portal/manage/{resource}` route +
  `manage.html` for instruments/schedules/programs/calibration/uploads/peers.
- **D3** `static/js/settings.js` + `access.html`/`import.html`/`fleet.html` +
  explicit routes (avoided a `/portal/{page}` catch-all that would shadow
  `/portal/data` and `/portal/system`).
- **D4** instrument row actions wired to existing endpoints: record / stop /
  diagnose (shows result) / live.
- **D5** tests -- pages render + are login-gated; unknown resource 404; assets
  served.

## Verification

Gate green: vulture/black/ruff/flake8/mypy (108 files)/pytest (**114 passed**).
Manual smoke: server restarted on v0.3.2; nav + console + settings pages load.

## Lessons

- The cookie-authenticated API meant the whole UI is thin JS islands over the
  *same* endpoints the API exposes -- no new server-side form handlers, no
  duplicated logic. CSP held because every script is an external file.
- A `/portal/{page}` catch-all silently shadows sibling single-segment routes;
  explicit routes are safer when other routers own paths under the same prefix.

## Tag

``v0.3.2`` at the UI commit; merged to ``main``.
