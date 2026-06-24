# Sprint 0.1-M0-S002 -- Callisto serial driver (class-1) + device simulator

**Sprint Goal:** Make a real Callisto receiver drivable through the
`InstrumentDriver` contract, provable end-to-end with no hardware.

**Full ID:** 0.1-M0-S002
**Version:** 0.1  **Milestone:** M0  **Theme:** first instrument driver
**Duration:** single-session (2026-06-24)
**Branch:** ``0.1-dev``
**Status note:** documented retroactively (sprint discipline adopted at S003).

## Trigger

S001 proved the seam with a synthetic driver. The next M0 step (ROADMAP) is the
class-1 heterodyne driver -- porting the legacy serial protocol behind the
contract so the design's "Callisto logic is just the first driver" holds.

## Decision

Split the driver into testable layers so the fiddly legacy protocol is captured
as **pure, vector-tested functions** rather than embedded in I/O:
`protocol.py` (pure) -> `parser.py` (incremental decoder) -> `driver.py`
(lifecycle over a `Connection` seam) -> `simulator.py` (in-memory device). The
`Connection` abstraction (device-side seam, DESIGN 5a) lets the same driver run
against the simulator in CI and real serial in production.

## Deliverables

| # | Task | Layer | Notes |
| -- | -- | -- | -- |
| D1 | `Connection` seam | core | byte-oriented device link protocol (serial/USB/network) |
| D2 | `protocol.py` (pure) | drivers | firmware detect, divider/band math, command builders, 8-bit norm |
| D3 | `parser.py` | drivers | incremental decoder: text messages vs STX-hex sweeps |
| D4 | `CallistoDriver` + simulator | drivers | full lifecycle; in-memory Callisto for hardware-free tests |
| D5 | Tests | tests | protocol vectors + end-to-end record against the simulator |

## Acceptance Criteria

- [x] `CallistoDriver` satisfies `InstrumentDriver`.
- [x] Firmware 1.5/1.7/1.8 detected; channel command matches legacy vector.
- [x] End-to-end record yields normalized 8-bit `SpectrumFrame`s (RAW).
- [x] Quality gate green; 20 tests pass.

## Out of Scope

FITS output; acquisition loop; real serial backend (pyserial); calibration.

## Tag target

None (M0 in progress).
