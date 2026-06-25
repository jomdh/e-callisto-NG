# ADR-0004 — OutputWriter takes a Recording, not loose frames

**Status:** Accepted

## Context

The initial `OutputWriter.write(frames, unit, out_dir)` was insufficient: a FITS
file also needs the **frequency axis** (per-channel `Channel`s -- frames carry
only sample values) and **station metadata** (instrument, origin, lat/lon/alt,
frqfile, PWM, focus) for the header. Threading these as extra positional
arguments would bloat the contract and every writer.

## Decision

Introduce a `Recording` value object in `core` bundling
`{meta, channels, frames, sample_rate_hz, unit}` and refine the contract to:

```
filename(recording) -> str
write(recording, out_dir) -> Path
```

`CONTRACT_VERSION` bumped 0.1.0 -> 0.2.0.

## Rationale

- One cohesive input that any writer (legacy/standard/custom) consumes; adding a
  field later does not change the signature.
- `Recording`/`RecordingMeta` are frozen dataclasses, so `core` stays
  dependency-free.
- This is the intended discipline for the plugin seam: a contract change is a
  deliberate, versioned, ADR-recorded act (CLAUDE load-bearing principle).

## Consequences

- Only `OutputWriter` had no implementations yet, so blast radius is nil beyond
  the contract; `StandardFitsWriter` (S003) is the first implementation.
- The acquisition loop (S004) assembles a `Recording` from a driver's frames +
  configured channels + station metadata and hands it to a writer.

Reference: DESIGN 6a, 6b; CONTRACT_VERSION in `core/contracts.py`.
