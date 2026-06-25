# Sprint 0.5-M15-S039 -- config backup/restore + system info (M15 close)

**Goal:** Config backup/restore, system-info, and a Settings page.
**Full ID:** 0.5-M15-S039  **Milestone:** M15 (final)  **Branch:** `0.5-dev`  **Status:** Completed.

## Deliverables
- `services/config_backup.py` export/import (config tables only, FK-safe).
- `/api/v1/system/info` (version/disk/clock/retention); `/api/v1/config/export`
  + `/import` (admin).
- `/portal/settings` page + nav (system info + backup/restore).

## Acceptance
- [x] Config round-trips (incl. datetime); admin-only; system info returns disk/clock.
- [x] Settings page renders. Gate green; M15 tagged v0.5.0.

## Deferred (to backlog)
Reboot/shutdown + journald log viewer (host-level, needs least-priv hook) and
data-browser depth (calendar/FITS viewer/bulk ops) -> FEATURE_BACKLOG.
