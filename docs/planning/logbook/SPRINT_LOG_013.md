# Sprint 0.1-M3-S013 -- sun-relative scheduler (M3 close)

**Status:** Completed (2026-06-25)  **Branch:** ``0.1-dev``

## Goal / Met?

Schedule recordings to follow the Sun. **Met** -- astropy computes
sunrise/transit/sunset; the daily window and recording-now decision are pure and
tested; schedules are CRUD-able with a preview.

## Actions Taken

- **D1 `services/scheduler.py`** -- `sun_events` (altitude grid + zero-crossings,
  handles polar via None), `sun_window` (margins), `is_recording_desired`.
- **D2** `Schedule` model (per-instrument, sun/fixed, margin).
- **D3 `routes/schedules.py`** -- list/create/delete + `/preview` (today's window
  + recording_now).
- **D4 tests** -- equator-equinox ephemeris sanity, window/desire at noon vs
  midnight, schedule CRUD + preview.

## Verification

Gate green: vulture/black/ruff/flake8/mypy (63 files)/pytest (**58 passed**).

## Milestone M3 -- complete

S012-S013 logged. Operators define frequency programs (manual or overview-
generated) and sun-relative schedules with a preview. Version -> v0.1.3;
changelog; tag `v0.1.3`; pushed.

## Lessons

- astropy's altitude-grid + zero-crossing approach gives correct rise/set without
  a dedicated rise/set routine; 10-min sampling is plenty for scheduling and
  keeps the call ~sub-second. Polar day/night fall out as missing crossings.
- Deferred: the background loop that actually starts/stops the recorder on the
  schedule. The decision logic is done and tested; wiring it to the recorder
  thread is a thin refinement (and overlaps M4 health/auto-run).

## Tag

``v0.1.3`` at the M3-complete commit on ``0.1-dev``.
