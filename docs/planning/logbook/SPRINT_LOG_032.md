# Sprint 0.4-M12-S032 -- BenchCapable contract + detector bench

**Status:** Completed (2026-06-25)  **Branch:** `0.4-dev`

## Goal / Met?
Bench primitives + detector readout. **Met** -- `BenchCapable` (ADR-0005) added
as an optional protocol; Callisto + Fake implement it; detector read + sweep
services + endpoints work hardware-free.

## Actions
- ADR-0005 + index; `core.contracts.BenchCapable` + CONTRACT_VERSION 0.3.0;
  exported from `core`.
- FakeDriver synthetic detector (deterministic bandpass x gain + relay offset);
  CallistoDriver tune/set_gain/read_detector/set_relay + protocol builders +
  `parse_detector`.
- `services/bench.py`; bench detector + sweep endpoints (capability-gated).

## Verification
Gate green: vulture/black/ruff/flake8/mypy (114 files)/pytest (**129 passed**).

## Lessons
- An *additive optional* protocol (not extending InstrumentDriver) kept every
  existing/SDR driver valid -- `isinstance(driver, BenchCapable)` cleanly gates
  the Tools pages per instrument class.

## Tag
None (M12 closes at S033).
