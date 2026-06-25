# Sprint 0.4-M12-S032 -- BenchCapable contract + detector bench

**Goal:** The bench primitives + detector readout (legacy `simple`).
**Full ID:** 0.4-M12-S032  **Milestone:** M12  **Branch:** `0.4-dev`  **Status:** Completed.

## Deliverables
- ADR-0005: `BenchCapable` optional driver protocol (tune/set_gain/read_detector/
  set_relay); CONTRACT_VERSION 0.2.0 -> 0.3.0.
- FakeDriver synthetic detector (bandpass x gain + relay); CallistoDriver bench
  primitives (F0/O/A0/fs) + `parse_detector`.
- `services/bench.py` (read_detector, sweep); `GET .../bench/detector`,
  `POST .../bench/sweep` (gated on BenchCapable, 409 while recording).

## Acceptance
- [x] Callisto is BenchCapable, SDR is not; detector responds to freq/gain/relay.
- [x] Endpoints work; non-bench instrument -> 400. Gate green.
