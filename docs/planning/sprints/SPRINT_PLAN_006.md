# Sprint 0.1-M1-S006 -- auth: users, sessions, RBAC

**Sprint Goal:** Let a user log in and have every request carry an authenticated
identity with a role, so the rest of M1 can be access-controlled.

**Full ID:** 0.1-M1-S006  **Milestone:** M1  **Branch:** ``0.1-dev``  **Status:** Planned.

## Decision

Argon2id password hashing; **server-side sessions** (DB table) keyed by a random
token in an HttpOnly SameSite cookie -- no JWT, simplest to revoke. Roles
admin > operator > viewer; `require_role(min)` dependency. No default
credentials (admin is created by the wizard/CLI later).

## Deliverables (5)

| # | Task | Layer | Notes |
| -- | -- | -- | -- |
| D1 | `api/models.py`: `User`, `Session`, `Role` | api | SQLModel tables; role enum |
| D2 | `api/security.py`: argon2 hash/verify; token mint | api | argon2-cffi PasswordHasher |
| D3 | `api/auth.py`: login/logout, `get_current_user`, `require_role` | api | cookie session; role hierarchy |
| D4 | `api/routes/auth.py`: POST /login /logout, GET /me; wire router | api | + `create_user` service helper |
| D5 | tests + logbook | tests | login/me/logout flow; RBAC denial |

## Acceptance Criteria

- [ ] Create user -> login sets session cookie -> `/me` returns identity -> logout clears it.
- [ ] `require_role(admin)` rejects a viewer (403) and an anonymous request (401).
- [ ] Passwords stored as argon2 hashes; no plaintext.
- [ ] Gate green; tests pass.

## Out of Scope

Portal login page (S008), wizard, 2FA, lockout (later).
