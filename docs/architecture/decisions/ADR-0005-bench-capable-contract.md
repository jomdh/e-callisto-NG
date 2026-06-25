# ADR-0005 -- BenchCapable: an optional bench/commissioning driver contract

**Status:** Accepted  **Date:** 2026-06-25  **Milestone:** M12

## Context

Legacy parity (M12) needs the bench/commissioning behaviours of the Windows
`simple` and `NoiseFigurePlotter` tools: tune a single frequency, set gain, read
the detector voltage, and switch the focus/relay tree. These are **commissioning**
operations, not the streaming-spectra path that `InstrumentDriver` models.

Two ways to add them:
1. Extend `InstrumentDriver` with `tune`/`set_gain`/`read_detector`/`set_relay`.
2. Add a **separate optional protocol** a driver may also implement.

Option 1 forces every driver -- including SDR class-2/3 and any closed third-party
driver -- to implement bench primitives that may not apply, and is a breaking
change to a shipped contract.

## Decision

Add a new `BenchCapable` `Protocol` to `core/contracts.py`, **independent of**
`InstrumentDriver`. A driver MAY implement both. Bench services accept a
`BenchCapable` and the API checks `isinstance(driver, BenchCapable)` (the
protocol is `runtime_checkable`), returning a clear error when an instrument
doesn't support bench mode.

```
tune(frequency_mhz: float) -> None      # legacy F0
set_gain(pwm: int) -> None              # legacy O
read_detector() -> float                # legacy A0, millivolts
set_relay(code: int) -> None            # legacy fs (focus/relay)
```

`CONTRACT_VERSION` 0.2.0 -> **0.3.0** (additive minor bump: existing
`InstrumentDriver` implementations are unaffected).

## Consequences

- The Callisto (heterodyne) driver implements `BenchCapable`; SDR drivers may
  later, or not. No existing driver breaks.
- Bench/NF services and the Tools pages are gated on the capability, surfaced to
  the operator (a non-bench instrument shows the tools as unavailable).
- The detector unit is **millivolts** throughout, matching the legacy AD8307
  detector readouts; the bench pages render via the M3 theme tokens (not the
  legacy palette).
