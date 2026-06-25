# Sprint 0.4-M11-S030 -- data-loss watchdog + light-curve fidelity

**Status:** Completed (2026-06-25)  **Branch:** ``0.4-dev``

## Goal / Met?

Legacy recorder robustness + LC format. **Met** -- the watchdog stops a corrupt
recording, alerts with the verbatim legacy lines, and writes the good frames;
light curves use the legacy file name/format with the 10-channel cap.

## Actions Taken

- **D1** `services/watchdog.py` -- `Watchdog.check()` (out-of-range ⇒ corrupt),
  `alert_sequence()` (`Auto stop due to data loss.` / `Check RS232-connection!` /
  `Attempting Auto-Start`), `DataLossError`. Wired into `record()` (stop early,
  write good frames, callback; raise if zero good frames) and the recorder (logs
  + `RecorderStatus.messages`). The scheduler re-arm is the auto-start.
- **D4** rewrote `lightcurve.py` -- `LC<YYYYMMDD>_<ADU|SFU|KEL>_<instrument>.txt`,
  10-channel cap, fractional-UT-hour time column (feeds the M13 PNG renderer).

## Verification

Gate green: vulture/black/ruff/flake8/mypy (110 files)/pytest (**119 passed**).
Updated the M5 LC test to the new format.

## Lessons

- Making the watchdog a pure `check()` + `alert_sequence()` kept it fully
  unit-testable; the "auto-restart" needs no new code -- the M6 scheduler already
  re-arms a desired-but-not-recording instrument each tick.
- Writing the *good* frames on data loss (rather than discarding) is the
  degrade-don't-die behaviour (DESIGN 14a): no science is lost to a glitch.

## Tag

None (M11 closes at S031).
