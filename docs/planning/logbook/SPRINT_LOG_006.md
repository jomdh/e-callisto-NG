# Sprint 0.1-M1-S006 -- auth: users, sessions, RBAC

**Status:** Completed (2026-06-25)  **Branch:** ``0.1-dev``

## Goal / Met?

Let a user log in and carry an authenticated identity + role. **Met** -- login
sets a server-side session cookie, `/me` returns the identity, logout revokes it,
and `require_role` enforces the hierarchy.

## Actions Taken

- **D1 `api/models.py`** -- `User`, `Session`, `Role` (StrEnum viewer<operator<
  admin) + `role_satisfies`.
- **D2 `api/security.py`** -- argon2id `hash_password`/`verify_password`;
  `new_session_token` (urlsafe 32B); cookie name + TTL.
- **D3 `api/auth.py`** -- `create_user`, `login`/`logout`, `get_current_user`
  (HttpOnly cookie -> session lookup -> expiry check), `require_role` factory.
- **D4 `api/routes/auth.py`** -- POST /login, POST /logout, GET /me; wired into
  `create_app`; models imported so tables register.
- **D5 tests** -- `conftest.py` (client + temp-DB fixtures), `test_auth.py`
  (login/me/logout, anon 401, RBAC 401/403/200).

## Verification

Gate green: vulture/black-79/ruff (ignore B008 for FastAPI Depends)/flake8/mypy
(42 files)/pytest (**34 passed**).

## Lessons

- B008 (call-in-default) is a structural false positive for FastAPI; ignoring it
  project-wide is correct rather than per-line noqa.

## Tag

None (M1 in progress).
