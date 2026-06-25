# Sprint 0.5-M15-S038 -- users & audit log

**Status:** Completed (2026-06-25)  **Branch:** `0.5-dev`

## Goal / Met?
User management + audit. **Met** -- admins manage accounts (create/role/disable/
delete) and review an append-only audit log of security-sensitive actions.

## Actions
- ADR-0006 (append-only audit) + index; `AuditEvent` model; `services/audit.py`
  record (best-effort, never blocks the action, no secrets).
- `routes/users.py`: user CRUD + `/api/v1/audit` (admin); audit on
  create/role/disable/delete; login.ok / login.fail audited in `auth.login`.
- console `users` resource (role select); `/portal/audit` page + settings.js
  audit view; Users + Audit nav links.

## Verification
Gate green: vulture/black/ruff/flake8/mypy (126 files)/pytest (**156 passed**).

## Lessons
- A single best-effort `audit.record` keeps audit calls one-liners at each call
  site and guarantees a failed audit write never breaks the audited action.

## Tag
None (M15 closes at S039).
