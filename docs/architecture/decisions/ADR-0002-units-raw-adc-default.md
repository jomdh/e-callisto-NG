# ADR-0002 — Raw ADC is the default unit; dB and calibration are opt-in

**Status:** Accepted

## Context

The legacy tools auto-convert samples to dB for display, conflating a log
*estimate* with a physical *calibration*. For a scientific archive this is a
hazard: stored values must be unambiguous.

## Decision

**Raw ADC / digits is always the default** for stored data and displays. Three
explicit levels, defaulting to the rawest:

1. **Raw ADC** — default, requires nothing.
2. **dB** — optional log-scaled *estimate*, never automatic; a per-instrument /
   per-view toggle. Never the stored unit.
3. **Calibrated (SFU / Kelvin)** — requires an explicit calibration + coefficients.

The suite never silently transforms values, and every product records which
level produced it (`UnitLevel`, default `RAW`).

## Consequences

- `SpectrumFrame.unit` defaults to `UnitLevel.RAW`; drivers emit raw samples.
- Output Writers honor the frame unit and bit depth; the Legacy writer may
  downscale to 8-bit for archive compatibility but does not invent dB.
- Live viewers default to raw/linear; dB and SFU/Kelvin are explicit toggles.

Reference: DESIGN section 6b.
