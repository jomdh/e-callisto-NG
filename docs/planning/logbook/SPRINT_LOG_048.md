# Sprint 0.7-M21-S048 -- DB-backed recorder run-state (cross-process)

**Status:** Completed (2026-06-25)  **Branch:** `0.7-dev`

## Goal / Met?
Cross-process recorder status (F14). **Met** -- recorder state persists to the
DB, so the web app sees recordings the `acquire` daemon owns.

## Actions
- `RecorderRuntime` table; `services/recorder_state.write/read`.
- `recorder.start(on_state=...)` callback fired on RECORDING/IDLE/ERROR; the
  recorder stays api-free, the API callers (record route + scheduler) wire a
  DB-persisting callback.
- `instrument_cockpit` prefers the persisted runtime, falling back to the local
  in-memory recorder view.

## Verification
Gate green: vulture/black/ruff/flake8/mypy (142 files)/pytest (**192 passed**).

## Lessons
- The callback keeps the recorder usable from the CLI (no DB) while the web/daemon
  paths persist -- the layering (recorder api-free) holds.

## Tag
None (M21 closes at S049).
