# Sprint 0.7-M21-S049 -- host control hooks + System UI (M21 close)

**Goal:** journald/log viewer, reconnect, reboot/shutdown, update apply/rollback
behind a least-privilege hook (ADR-0008). Closes M21.
**Full ID:** 0.7-M21-S049  **Milestone:** M21 (final)  **Branch:** `0.7-dev`  **Status:** Completed.

## Deliverables
- ADR-0008 (least-priv host hook, closed verb set); `host_hook`/`log_file` settings.
- `services/host` (tail_log read-only; run_hook with closed verbs).
- endpoints: `/system/log`, `/system/reboot`, `/shutdown`, `/update/apply`,
  `/update/rollback` (admin); `/instruments/{id}/reconnect` (operator) -- all audited.
- System page: host-control buttons + log tail (`system.js`).

## Acceptance
- [x] Hook disabled by default + clear message; fake hook invoked with verb;
      actions audited; admin-only; log tail works. Gate green; M21 -> v0.7.1.
