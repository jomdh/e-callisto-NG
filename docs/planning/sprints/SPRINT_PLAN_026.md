# Sprint 0.3-M9-S026 -- class-2 SDR driver (host DSP)

**Sprint Goal:** Record from an SDR whose channelization runs in host software,
through the exact same pipeline as the heterodyne receiver.

**Full ID:** 0.3-M9-S026  **Milestone:** M9  **Branch:** ``0.2-dev``  **Status:** Planned.

## Decision

`SoftSdrDriver` implements the `InstrumentDriver` contract and does the DSP on the
host: synth IQ -> FFT -> normalized 8-bit power spectra. Hardware-free (synthetic
IQ); a real build swaps the IQ source for SoapySDR/librtlsdr. This is the proof
that the M0 seam absorbs a fundamentally different instrument class with no
downstream change.

## Deliverables (4)

| # | Task | Layer | Notes |
| -- | -- | -- | -- |
| D1 | `drivers/sdr/soft.py` `SoftSdrDriver` | drivers | FFT host DSP; SDR_SOFT/HOST/USB caps |
| D2 | register `sdr_soft` in `build_driver` | services | by instrument class |
| D3 | tests | tests | conforms; streams normalized spectra; records to FITS via API |
| D4 | logbook | docs | -- |

## Acceptance Criteria

- [ ] `SoftSdrDriver` conforms; capabilities = SDR_SOFT/HOST.
- [ ] Streams normalized 8-bit spectra with structure (FFT).
- [ ] An `sdr_soft` instrument records to FITS through the same recorder.
- [ ] Gate green; SNR clean.

## Out of Scope

Class-3 FPGA driver + network backend (S027); real SDR hardware; band/tuning UI.
