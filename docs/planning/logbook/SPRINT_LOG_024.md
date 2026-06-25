# Sprint 0.2-M8-S024 -- legacy import

**Status:** Completed (2026-06-25)  **Branch:** ``0.2-dev``

## Goal / Met?

Import an existing station's config. **Met** -- pure parsers read the four legacy
formats; the import endpoint creates Station/Instrument/Program/CalibrationSet/
Schedule (and assigns the calibration); dry-run previews without writing.

## Actions Taken

- **D1** `services/legacy_import.py` -- `parse_callisto_cfg` (identity + signed
  lat/lon), `parse_frequency_program` (channel freqs + nsweeps + LO),
  `parse_calibration_prn` ([a,b,cf,Tb] rows), `parse_scheduler_cfg` (entries).
- **D2** `routes/migrate.py` POST `/api/v1/import` -- builds NG records;
  legacy scheduler -> a fixed window (earliest start, latest stop); `dry_run`
  returns a summary only.
- **D3** tests -- each parser against legacy samples + endpoint creates records +
  dry-run creates nothing.

## Verification

Gate green: vulture/black/ruff/flake8/mypy (94 files)/pytest (**93 passed**).

## Lessons

- In-place FITS indexing needed no work: the scan-based catalog (M2) already
  lists whatever sits in the data dir, so pointing a migrated station's data dir
  at its legacy FITfiles surfaces history immediately.

## Tag

None (M8 closes at S025 with the v0.2 version close).
