# Sprint 0.2-M6-S020 -- calibration wiring + light curves (M6 close)

**Status:** Completed (2026-06-25)  **Branch:** ``0.2-dev``

## Goal / Met?

Calibrated output + light curves. **Met** -- an instrument with `unit=sfu` and a
calibration set records BUNIT=sfu FITS (via API and scheduler); flagged channels
produce a light-curve CSV; raw stays the default.

## Actions Taken

- **D1** `CalibrationSet` model; `Instrument.unit`/`calibration_set_id`/
  `file_seconds`; `routes/calibration.py` CRUD.
- **D2** `record()` + `recorder.start` accept `unit`/`calibration`;
  `calibration_build.build_calibration` + `resolve` (raw unless a calibrated unit
  *and* coefficients).
- **D3** record route + scheduler `_start` resolve the instrument's calibration
  and pass it through.
- **D4** `services/lightcurve.py` `write_light_curves` (CSV for flagged channels)
  called from `record()`; no flag -> no file.
- **D5** tests -- calibrated FITS via API; LC written for flagged / omitted
  otherwise.

## Verification

Gate green: vulture/black/ruff/flake8/mypy (83 files)/pytest (**76 passed**).

## Milestone M6 -- complete

S018-S020 logged. The station now records on schedule, uploads automatically,
prunes by retention, applies calibration, and emits light curves -- genuinely
unattended. Version -> v0.2.0; tag v0.2.0; pushed.

## Lessons

- Threading `unit`/`calibration` as optional params (default raw/None) kept every
  existing call site working and preserved raw-by-default (6b) -- the calibrated
  path is purely additive.
- A pure `resolve(unit_str, coeffs, n)` shared by the route and the scheduler
  avoided duplicating the "is this calibrated?" decision.

## Tag

``v0.2.0`` at the M6-complete commit on ``0.2-dev``.
