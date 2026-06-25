# Sprint 0.7-M21-S049 -- host control hooks + System UI (M21 close)

**Status:** Completed (2026-06-25)  **Branch:** `0.7-dev`

## Goal / Met?
Host operations from the portal (F12 + F15). **Met** -- log viewer, receiver
reconnect, guarded reboot/shutdown, and update apply/rollback, all through a
least-privilege hook, audited.

## Actions
- ADR-0008 + index: single configured `host_hook` + closed verb set
  (reconnect/reboot/shutdown/update/rollback); web stays unprivileged; log
  viewing tails a file read-only (no hook).
- `services/host.py` tail_log + run_hook (verb validation, disabled-by-default).
- `host_hook`/`log_file` settings; endpoints (admin host actions + operator
  reconnect) each `audit.record`'d; System page buttons + log tail via system.js.

## Verification
Gate green: vulture/black/ruff/flake8/mypy (144 files)/pytest (**200 passed**).

## Milestone M21 -- complete
S048-S049. Cross-process recorder status (F14) + host control & lifecycle
(F12+F15) -- the host now fully manageable from the portal without granting the
web process privilege. Version -> v0.7.1; tag.

## Lessons
- A closed verb set + a single configured hook is the whole security story: no
  user input ever becomes a shell string, and host actions are off until an
  admin installs the hook with scoped privileges.

## Tag
`v0.7.1` at the M21-complete commit on `0.7-dev`.
