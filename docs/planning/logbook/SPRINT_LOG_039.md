# Sprint 0.5-M15-S039 -- config backup/restore + system info (M15 close)

**Status:** Completed (2026-06-25)  **Branch:** `0.5-dev`

## Goal / Met?
Settings depth. **Met** -- config backup/restore, a system-info endpoint, and a
Settings page (version, disk, clock, retention + backup/restore).

## Actions
- `services/config_backup.py` export_config / import_config over the config
  tables (calibration, programs, station, instruments, schedules, targets,
  access, peers); FK-safe order; model_validate coerces JSON datetimes; excludes
  accounts/sessions/audit/jobs.
- `/api/v1/system/info`; `/api/v1/config/export` + `/import` (admin).
- `/portal/settings` page + settings.js (sysinfo + download/restore); nav link.

## Verification
Gate green: vulture/black/ruff/flake8/mypy (128 files)/pytest (**161 passed**).

## Milestone M15 -- complete
S038-S039. Station Settings depth: user management + audit log (S038), config
backup/restore + system info + Settings page (S039). Version -> v0.5.0; tag.

## Deferred (honest SNR)
Host-level reboot/shutdown + journald log viewer (need a least-privilege hook,
risky to auto-run) and data-browser depth (calendar/in-browser FITS/bulk ops)
moved to FEATURE_BACKLOG (F12, F13) rather than half-built.

## Tag
`v0.5.0` at the M15-complete commit on `0.5-dev`.
