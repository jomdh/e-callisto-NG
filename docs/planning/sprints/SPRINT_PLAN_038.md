# Sprint 0.5-M15-S038 -- users & audit log

**Goal:** User management UI + append-only audit log (DESIGN 8.4 / ADR-0006).
**Full ID:** 0.5-M15-S038  **Milestone:** M15  **Branch:** `0.5-dev`  **Status:** Completed.

## Deliverables
- ADR-0006 + index; `AuditEvent` model; `services/audit.record` (best-effort).
- `routes/users.py` user CRUD (admin) + `/api/v1/audit`; audit on create/role/
  disable/delete + login ok/fail.
- console `users` resource; `/portal/audit` page + nav (Users, Audit).

## Acceptance
- [x] User CRUD admin-only; self-delete blocked; passwords never returned/audited.
- [x] Login + user actions audited; audit read admin-only. Gate green.
