# Sprint 0.1-M0-S003 -- standard-mode FITS output writer

**Sprint Goal:** Turn a stream of recorded spectra into a valid, archive-shaped
time x frequency FITS file on disk.

**Full ID:** 0.1-M0-S003
**Version:** 0.1  **Milestone:** M0  **Theme:** the write half of the record loop
**Duration:** single-session (planned 2026-06-25)
**Branch:** ``0.1-dev``
**Status:** Planned (awaiting go-ahead before execution).

## Trigger

S002 produces normalized `SpectrumFrame`s. M0's completion criterion is an
end-to-end recording (driver -> FITS on disk). This sprint builds the **writer**;
the acquisition loop + CLI that join driver and writer are the next sprint (S004).

## Decision

Implement the **Standard** output mode first (clean, conventional FITS via
astropy), not Legacy -- standard is the simpler, well-formed baseline; Legacy
byte-compatibility and Custom templates are later writers behind the same
contract (DESIGN 6a).

**Contract refinement (ADR-0004).** The current `OutputWriter.write(frames,
unit, out_dir)` is insufficient: a FITS file also needs the **frequency axis**
(per-channel `Channel`s -- frames carry only sample values) and **station
metadata** (instrument name, origin, lat/lon/alt, frqfile name, PWM/gain, focus
code) for the header. Introduce a `Recording` value object in `core` bundling
{frames, channels, meta, unit} and refine the contract to
`write(recording, out_dir) -> Path`. This is a deliberate, versioned contract
change (CONTRACT_VERSION bump + ADR) -- exactly the discipline the plugin seam
requires (CLAUDE "load-bearing principle").

## Deliverables (5 -- Rule 6 ok)

| # | Task | Layer | Notes |
| -- | -- | -- | -- |
| D1 | `core`: `RecordingMeta` + `Recording` models; refine `OutputWriter` contract to `write(recording, out_dir)`; bump `CONTRACT_VERSION`; update `FakeWriter`-less callers | core | frozen dataclasses; meta = instrument/origin/lat/lon/alt/frqfile/pwm/focus |
| D2 | ADR-0004 (OutputWriter takes a `Recording`) + index update in same change | docs | records the contract change + rationale |
| D3 | `writers/fits/standard.py`: `StandardFitsWriter` implementing the contract via astropy | writers | 8-bit BYTE_IMG time x freq, transposed low-freq-top; header DATE/TIME-OBS/-END, OBS_LAT/LON/ALT, FRQFILE, PWM_VAL, BUNIT=digits, CRVAL/CDELT axes; filename `INSTRUMENT_YYYYMMDD_HHMMSS_FC.fit` |
| D4 | Dependencies: add `astropy`/`numpy` to pyproject; keep `core` dep-free | infra | astropy is a `writers` dep, not a `core` dep |
| D5 | Tests: write frames -> read back with astropy; assert shape, dtype, key header cards, axis values, filename; + sprint logbook | tests/docs | round-trip a FakeDriver recording |

## Acceptance Criteria

- [ ] `StandardFitsWriter` satisfies the (refined) `OutputWriter` contract.
- [ ] A recording of N sweeps x C channels writes a FITS whose primary HDU is
  `(C, N)` 8-bit, low frequency on top, `BUNIT=digits`.
- [ ] Header carries DATE/TIME-OBS/-END, OBS_LAT/LON/ALT (+codes), FRQFILE,
  PWM_VAL; time axis (`CRVAL1` sec-of-day, `CDELT1` = 1/rate) and frequency
  axis (`CRVAL2`, channel list) present.
- [ ] Filename matches `INSTRUMENT_YYYYMMDD_HHMMSS_FC.fit`.
- [ ] Round-trip test reads the file back with astropy and checks values.
- [ ] `core` still imports nothing concrete (astropy confined to `writers`).
- [ ] Quality gate green; full suite passes.
- [ ] ADR-0004 + index updated in the same change as the contract edit.

## Out of Scope

- Legacy + Custom output modes (later writers).
- Acquisition loop, CLI, real pyserial backend (S004).
- Calibration (SFU/Kelvin), light curves, overview persistence.
- Upload/transport.

## Tag target

None (M0 in progress; M0 completes at S004 with the end-to-end CLI).
