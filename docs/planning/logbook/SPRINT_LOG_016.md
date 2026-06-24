# Sprint 0.1-M5-S016 -- calibration (SFU / Kelvin)

**Status:** Completed (2026-06-25)  **Branch:** ``0.1-dev``

## Goal / Met?

Optionally produce calibrated SFU/Kelvin FITS. **Met** -- `core/calibration.py`
implements the legacy per-channel transforms; the writer applies them when a
calibrated unit is chosen; raw stays the default.

## Actions Taken

- **D1 `core/calibration.py`** -- `ChannelCal`/`Calibration`; `to_sfu`/
  `to_kelvin` (clamped log-compression, ported from `FitsWrite.cpp`); pure.
- **D2** `Recording.calibration` (optional, default None); `_calibrate` in the
  writer applies per-channel SFU/Kelvin when `unit != RAW`, else raw.
- **D3** exported `Calibration`/`ChannelCal` from `core`.
- **D4 tests** -- math stays in 0..255 and monotone; raw vs SFU FITS differ with
  the right BUNIT.

## Verification

Gate green: vulture/black/ruff/flake8/mypy (74 files)/pytest (**66 passed**).

## Lessons

- Adding `calibration` as an optional `Recording` field kept it backward-
  compatible -- no contract break, just a richer payload. Raw-by-default (6b) is
  preserved because the writer only calibrates when explicitly asked.
- Deferred: CalibrationSet persistence + UI and wiring calibration into the live
  recorder path -- the science core is done and tested; the plumbing is thin.

## Tag

None (M5 closes at S017 with the version close).
