# ADR-0006 -- Append-only audit log for security-sensitive actions

**Status:** Accepted  **Date:** 2026-06-25  **Milestone:** M15

## Context

DESIGN 8.4 (Users & Access) calls for an **audit log**. Account changes, logins,
and other security-sensitive actions need a durable, tamper-evident-ish record an
admin can review. This is both a **schema change** and **security-sensitive
code**, so it gets an ADR.

## Decision

Add an `AuditEvent` table: `id`, `created_at`, `actor` (username or "system"),
`action` (a short verb, e.g. `user.create`, `login.fail`), `detail` (free text),
`target` (the affected entity, optional). Writes go through one helper
`services.audit.record(db, actor, action, detail, target)` -- **append-only**:
the app never updates or deletes audit rows, and there is no API to mutate them
(only an admin-only read endpoint).

Recorded actions for M15: user create / role-change / disable / delete, and login
success/failure. The list grows as later milestones add sensitive operations
(M17 update/restore, M15 reboot).

## Consequences

- Reads are admin-only; the table is never exposed for write via the API.
- Secrets are never written to `detail` (passwords, tokens) -- asserted in tests.
- Retention/rotation of the audit table is deferred (M17 storage policy); for now
  it grows unbounded, which is acceptable at station scale.
- The helper is synchronous and best-effort: an audit-write failure must not block
  the audited action from completing, but is logged.
