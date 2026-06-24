# Sprint 0.1-M0-S003 -- standard-mode FITS output writer

**Status:** Completed (2026-06-25)
**Date:** 2026-06-25
**Branch:** ``0.1-dev``

## Goal

Turn a stream of recorded spectra into a valid, archive-shaped time x frequency
FITS file on disk.

## Goal Met?

**Yes.** `StandardFitsWriter` writes a `Recording` to an 8-bit time x frequency
FITS (low frequency on top) with the standard header and a time/frequency
binary-table HDU; a round-trip test reads it back with astropy and verifies
shape, dtype, axes, and header cards.

## Decision

- Standard mode first (clean, conventional FITS); Legacy/Custom are later writers
  behind the same contract.
- **Contract refinement (ADR-0004):** `OutputWriter` now takes a `Recording`
  (meta + channels + frames + sample_rate + unit) instead of loose frames, since
  a FITS file needs the frequency axis and station metadata. `CONTRACT_VERSION`
  0.1.0 -> 0.2.0.

## Actions Taken

- **D1 core models + contract.** `core/recording.py` (`RecordingMeta`,
  `Recording`); refined `OutputWriter` to `filename(recording)` /
  `write(recording, out_dir)`; bumped `CONTRACT_VERSION`; exported from
  `core/__init__`.
- **D2 ADR-0004** + index update (same change).
- **D3 `writers/fits/standard.py`.** `StandardFitsWriter`: builds the (freq,
  time) uint8 image (transpose + freq flip), full header (DATE/TIME-OBS/-END,
  ORIGIN/INSTRUME/OBJECT, BZERO/BSCALE, BUNIT=digits, DATAMIN/MAX, CRVAL/CDELT
  axes, OBS_LAT/LON/ALT + codes, FRQFILE, PWM_VAL), and a binary-table HDU with
  the TIME and FREQUENCY vectors. Filename
  `INSTRUMENT_YYYYMMDD_HHMMSS_FC.fit`.
- **D4 deps.** Added `astropy`/`numpy` to pyproject (scoped to `writers`; `core`
  stays dep-free). Bumped tool targets to py312 (design target; also fixes numpy
  stubs under mypy). Converted `core` enums to `StrEnum`.
- **D5 tests + logbook.** `test_fits_writer.py` (contract conformance, filename,
  shape/dtype/axes round-trip, header cards, empty-recording rejection).

## Verification

Quality gate green: vulture, black-79, ruff (moved `select` under
`[tool.ruff.lint]`), flake8, mypy (23 files), pytest (**25 passed**) -- run in a
`.venv` with astropy 8.0.

## Lessons / Observations

- Filed **B1**: `sample_rate_hz` means sweeps/sec in `Recording` but is used as
  pixels/sec in `CallistoDriver.configure`. Reconcile in S004 when wiring the
  acquisition loop, so the FITS time axis is correct on the Callisto path.
- The contract refinement was painless precisely because the seam had no
  implementations yet -- doing it now (vs after several writers) is why the ADR
  discipline front-loads contract decisions.

## Tag

None (M0 completes at S004).
