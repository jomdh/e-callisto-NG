# Sprint 0.1-M4-S015 -- health checks + alerts (M4 close)

**Status:** Completed (2026-06-25)  **Branch:** ``0.1-dev``

## Goal / Met?

Show station health with alerts. **Met** -- a health report (disk, instruments,
recordings, upload backlog) with derived alerts, exposed via API and a portal
page.

## Actions Taken

- **D1 `services/health.py`** -- `compute_alerts` (pure: low disk / no
  instruments / upload backlog / bad clock), `disk_for`, `build_report`.
- **D2 `routes/system.py`** -- GET /api/v1/system/health + /portal/system;
  pending = recordings not in any done UploadJob.
- **D3** `templates/portal/system.html` (alerts + metric cards) + dashboard link.
- **D4 tests** -- alert logic table, endpoint (no-instruments alert), page render.

## Verification

Gate green: vulture/black/ruff/flake8/mypy (72 files)/pytest (**64 passed**).

## Milestone M4 -- complete

S014-S015 logged. Files upload to a configured target (manual run) and the
dashboard surfaces health. Version -> v0.1.4; changelog; tag `v0.1.4`; pushed.

## Lessons

- Clock-sync detection is genuinely platform-dependent; reporting it tri-state
  (and only alerting on known-bad) avoids false alarms while leaving room for a
  proper chrony/timedatectl probe later (DESIGN 12a).
- Deferred to refinement: auto-dispatch (immediate/scheduled) wiring of the
  uploader, and email/webhook alert delivery -- both thin layers over what's
  built.

## Tag

``v0.1.4`` at the M4-complete commit on ``0.1-dev``.
