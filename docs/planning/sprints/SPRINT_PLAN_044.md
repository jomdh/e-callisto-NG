# Sprint 0.6-M19-S044 -- left-sidebar shell + design system

**Goal:** Replace the top nav with doncel's left vertical sidebar + adopt the
updated shared M3 design system.
**Full ID:** 0.6-M19-S044  **Milestone:** M19  **Branch:** `0.6-dev`  **Status:** Completed.

## Deliverables
- Updated `material-design-system.css` (shared versioned asset, 1610 lines).
- `portal.css`: sidebar layout + compat shim (.muted, --surface aliases).
- `base.html` shell + `_sidebar.html` (Material Icons per section, grouped with
  labels/dividers, theme toggle, footer); `sidebar.js` (theme/collapse/mobile).
- Migrated every page off `_nav.html`/bespoke topbars; login/wizard chrome-less.

## Acceptance
- [x] Sidebar on authed pages, active highlight, icons, theme toggle; none pre-auth.
- [x] Gate green; 180 tests.
