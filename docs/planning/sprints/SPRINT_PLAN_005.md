# Sprint 0.1-M1-S005 -- FastAPI app skeleton + SQLite + settings + health

**Sprint Goal:** Stand up the web backbone -- a running FastAPI app with typed
settings, SQLite persistence, and a health endpoint -- that M1 builds on.

**Full ID:** 0.1-M1-S005
**Version:** 0.1  **Milestone:** M1  **Branch:** ``0.1-dev``
**Status:** Planned.

## Trigger

M0 delivered the record engine + CLI. M1 turns it into a web-operated station.
First the backbone: an app factory, settings, a DB, and a health probe -- before
auth, portal, and the wizard.

## Decision

FastAPI app-factory pattern (`create_app()`) for testability; `pydantic-settings`
for typed config from env (`.env`); SQLModel over SQLite (WAL) per design. The
`api` package owns all of this; it depends on `core`/`services`, never the
reverse.

## Deliverables (4)

| # | Task | Layer | Notes |
| -- | -- | -- | -- |
| D1 | deps: fastapi, uvicorn, sqlmodel, pydantic-settings, jinja2, argon2-cffi, httpx | infra | added to pyproject |
| D2 | `api/settings.py` | api | `Settings` (data_dir, config_dir, db_url, bind, port, secret_key); env-prefixed `ECALLISTO_` |
| D3 | `api/db.py` | api | SQLModel engine (SQLite WAL), `get_session`, `init_db()` |
| D4 | `api/app.py` + health + tests + logbook | api/tests | `create_app()`; `GET /api/v1/health` -> status/version/db; TestClient test |

## Acceptance Criteria

- [ ] `create_app()` returns a FastAPI app; `GET /api/v1/health` returns 200 with
  `{status, version, db}`.
- [ ] Settings load from env with `ECALLISTO_` prefix and sane defaults.
- [ ] SQLite engine initializes; health confirms a DB round-trip.
- [ ] `core` unchanged; `api` depends inward only.
- [ ] Quality gate green; tests pass.

## Out of Scope

Auth, RBAC, portal templates, wizard, instrument CRUD (later M1 sprints).

## Tag target

None (M1 in progress).
