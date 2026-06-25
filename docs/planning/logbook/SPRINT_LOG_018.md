# Sprint 0.2-M6-S018 -- scheduler drives recording

**Status:** Completed (2026-06-25)  **Branch:** ``0.2-dev``

## Goal / Met?

Record on the schedule with no operator action. **Met** -- `SchedulerService.tick`
starts a recording when inside the sun/fixed window and stops it when the window
closes; verified a file lands at noon (equator) and nothing starts at midnight.

## Actions Taken

- **D1** `Instrument.file_seconds`; `scheduler.fixed_window` (HH:MM -> today's
  UTC window).
- **D2** `services/scheduler_service.py` `SchedulerService.tick(db, now)` --
  per enabled schedule: compute window (sun/fixed), `is_recording_desired`, then
  start/stop the recorder; file-period rollover is implicit (re-arm on next tick).
- **D3** background loop + `settings.scheduler_tick_seconds` (0 = off).
- **D4** wired into app lifespan (start/stop loop); conftest sets tick=0;
  `test_api_health` moved to the shared client fixture.
- **D5** test: tick records inside window only.

## Verification

Gate green: vulture/black/ruff/flake8/mypy (77 files)/pytest (**70 passed**).

## Lessons

- Re-arming a bounded recording each tick gives file rollover for free -- no need
  for a true-continuous recorder yet.
- Adding a lifespan side effect (the loop) broke a test that bypassed the shared
  fixture; consolidating on the fixture (env: tick=0, temp data dir) fixed it and
  removed duplication.

## Tag

None (M6 closes at S020).
