# Sprint 0.1-M1-S007 -- instruments: model, CRUD, record control

**Status:** Completed (2026-06-25)  **Branch:** ``0.1-dev``

## Goal / Met?

Register instruments and start/stop a recording via the API, file on disk.
**Met** -- CRUD with RBAC; POST /record runs a background recording that lands a
FITS; /status reports IDLE + path; /stop interrupts.

## Actions Taken

- **D1 models.** `Station` (single-row host + observatory + coordinates),
  `Instrument` (class/address/focus/gain/channels/sweep_rate/enabled).
- **D2 `services/recorder.py`.** `RecorderService` (process-wide, locked) runs
  `record()` on a daemon thread; `stop()` calls `driver.stop()` to flush a
  partial FITS; `build_driver` picks Callisto (serial address) or FakeDriver.
- **D3/D4 `api/routes/instruments.py`.** CRUD (viewer reads / operator writes) +
  `/record`, `/stop`, `/status`; wired into the app.
- **D5 tests.** CRUD + RBAC (viewer 403 on create); record -> IDLE with an
  existing file. conftest now sets a temp data dir and clears the recorder
  between tests.

## Verification

Gate green: vulture/black/ruff/flake8/mypy (45 files)/pytest (**36 passed**).

## Lessons

- The recorder is a process-wide singleton, so tests must clear it between runs
  (added to the client fixture) -- a reminder that global service state needs an
  explicit test-isolation seam.
- Continuous + live-streamed recording is intentionally deferred to M2; this
  thread-per-recording baseline satisfies the M1 start/stop criterion.

## Tag

None (M1 in progress).
