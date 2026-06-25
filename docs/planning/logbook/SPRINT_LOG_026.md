# Sprint 0.3-M9-S026 -- class-2 SDR driver (host DSP)

**Status:** Completed (2026-06-25)  **Branch:** ``0.2-dev``

## Goal / Met?

Record from a host-DSP SDR through the same pipeline. **Met** -- `SoftSdrDriver`
synthesizes IQ, runs an FFT on the host, and delivers normalized spectra; an
`sdr_soft` instrument records to FITS through the unchanged recorder/writer.

## Actions Taken

- **D1** `drivers/sdr/soft.py` `SoftSdrDriver` -- InstrumentDriver lifecycle;
  `_dsp_frame` does synth-IQ -> FFT -> log -> 0..255; caps SDR_SOFT / HOST / USB,
  bit_depth 8.
- **D2** `build_driver` selects `sdr_soft` by instrument class.
- **D3** tests -- contract conformance + capabilities; structured streamed
  spectra; record an `sdr_soft` instrument to a (32 x 6) FITS via the API.

## Verification

Gate green: vulture/black/ruff/flake8/mypy (100 files)/pytest (**101 passed**).

## Lessons

- The seam held exactly as designed (DESIGN 5a): a class-2 SDR -- different physics,
  host DSP instead of a swept tuner -- dropped in as a driver with **zero** change
  to the recorder, writer, scheduler, or API. The boundary at "normalized spectra"
  paid off.
- Matching the contract's `configure(channels, sample_rate_hz)` signature exactly
  (names included) matters: mypy checks Protocol conformance by keyword.

## Tag

None (M9 closes at S027).
