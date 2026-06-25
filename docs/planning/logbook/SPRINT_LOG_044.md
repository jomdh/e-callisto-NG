# Sprint 0.6-M19-S044 -- left-sidebar shell + design system

**Status:** Completed (2026-06-25)  **Branch:** `0.6-dev`

## Goal / Met?
doncel-style left sidebar. **Met** -- a fixed left vertical menu with section
icons, grouped labels/dividers, theme toggle, collapse + mobile drawer, replaces
the top nav across the portal; the shared M3 design system is updated.

## Actions
- Adopted doncel's `material-design-system.css` (shared versioned asset).
- New `portal.css`: `body` flex shell, `.sidebar`/`.nav-link`/`.nav-divider`/
  `.theme-toggle`/`.app-main`, collapsed + mobile-drawer states; compat shim for
  `.muted` and `--surface`/`--surface-variant` (mapped to md-sys tokens) so
  existing page styles keep working.
- `base.html` renders the sidebar only when `user` is present (login/wizard stay
  chrome-less); `_sidebar.html` with Material Icons per section (Operations /
  Configure / Tools / Distribution / Administration), active via `request.url.path`.
- `sidebar.js`: nebula/supernova theme toggle, header-click collapse (persisted),
  mobile FAB drawer.
- Removed `_nav.html` + bespoke topbars from data/live/system; deleted `_nav.html`.

## Verification
Gate green: vulture/black/ruff/flake8/mypy/pytest (**180 passed**). Manual smoke:
sidebar + active highlight + icons render; assets 200; login has no sidebar.

## Lessons
- Keeping each page's inner `.portal-main` container and only stripping the nav
  meant the migration touched layout once (base) instead of every page body.
- CSP: doncel pulls HTMX from a CDN (blocked by our `script-src 'self'`); we keep
  vanilla JS islands, so only the visual shell was adopted, not the JS stack.

## Tag
None (M19 closes at S045).
