# Sprint 0.1-M1-S005 -- FastAPI app skeleton + SQLite + settings + health

**Status:** Completed (2026-06-25)
**Date:** 2026-06-25
**Branch:** ``0.1-dev``

## Goal

Stand up the web backbone -- a running FastAPI app with typed settings, SQLite
persistence, and a health endpoint -- that M1 builds on.

## Goal Met?

**Yes.** `create_app()` builds the app; `GET /api/v1/health` returns
`{status, version, db}` and confirms a SQLite round-trip via a temp DB in tests.

## Actions Taken

- **D1 deps.** fastapi, uvicorn, sqlmodel, pydantic-settings, jinja2,
  argon2-cffi (runtime) + httpx (dev, TestClient) added to pyproject.
- **D2 `api/settings.py`.** `Settings` via pydantic-settings, `ECALLISTO_`
  prefix, `.env` honored; data_dir/config_dir/db_url/bind/port/secret_key.
- **D3 `api/db.py`.** SQLModel engine (SQLite WAL + foreign_keys pragma),
  `init_db`, `get_session` dependency, `reset_engine_for_tests`.
- **D4 `api/app.py`.** App factory with a `lifespan` handler (init_db on start);
  `/api/v1/health`. `test_api_health.py` drives it through a temp DB.

## Verification

Gate green: vulture, black-79, ruff, flake8, mypy (35 files), pytest
(**31 passed**). Switched startup to the modern `lifespan` API (no deprecation).
`core` untouched; `api` depends inward only.

## Lessons / Observations

- Engine-reset + settings-cache-clear helpers make the app testable against a
  throwaway SQLite file without monkeypatching globals -- worth keeping as the
  pattern for all DB-touching tests.

## Tag

None (M1 in progress).
