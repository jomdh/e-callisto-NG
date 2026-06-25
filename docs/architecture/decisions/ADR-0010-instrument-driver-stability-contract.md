# ADR-0010 -- InstrumentDriver stability contract: typed faults + bounded liveness

**Status:** Accepted  **Date:** 2026-06-25  **Milestone:** M34

## Context

The load-bearing principle is that instrument instability stays **inside the
driver**: the engine above the seam (recorder, scheduler, API, UI) consumes
normalized spectra and never knows about serial ports, resets, or wire framing.
The structural seam exists -- `InstrumentDriver` is a `Protocol` in
`core/contracts.py`, `core` depends on nothing concrete, drivers live in
`drivers/*`. But the M34 stability research
(`docs/planning/research/callisto-stability-research.md`) found the seam is
**behaviourally porous** -- instability leaks across it three ways:

1. **No error taxonomy.** `core` defines no instrument error types, so a flaky
   device raises a raw `serial.SerialException`/`OSError` that propagates up into
   `services/acquisition.py` and `services/recorder.py`. The transport's failure
   mode crosses the seam naked.
2. **`stream()` makes no liveness promise.** Its contract is only *"Yield spectra
   … until stopped/closed."* A device that goes quiet but stays enumerated makes
   `stream()` spin on empty reads **forever** (`drivers/callisto/driver.py`
   stream loop; `islice` blocks in `acquisition.py`). The recorder thread hangs,
   status wedges in `RECORDING`, and nothing -- watchdog or scheduler -- can
   clear it. A driver-level stall becomes a system-level hang.
3. **Self-healing is in the wrong layer.** The legacy `reset -> init -> start`
   recovery (and the corruption test) belong inside the driver, which alone knows
   the protocol and cadence. Today they are absent; what passes for recovery is a
   full driver rebuild smeared into the **scheduler**. The driver does not own its
   own stability.

The legacy (both Borland and the Linux daemon) contained all of this **inside the
acquisition loop** -- a no-data timeout drove `reset/init/start`, a per-sample
high-bit test caught corruption, and a bounded reset guard escalated to the
supervisor. NG must offer the same containment, but expressed as a **contract**
so every driver -- including closed third-party SDR/FPGA drivers -- guarantees it.

## Decision

Strengthen the `InstrumentDriver` seam with a **fault taxonomy** and a
**bounded-liveness guarantee**, and make **self-healing the driver's
responsibility**.

### 1. Fault taxonomy (new, in `core`)

```
class InstrumentError(Exception): ...            # base for faults crossing the seam
class RecoverableInstrumentError(InstrumentError):
    """Transient fault the driver did/can retry. Mostly internal to the driver;
    a lifecycle call (connect/configure) MAY surface it to invite a cheap retry."""
class FatalInstrumentError(InstrumentError):
    """The driver cannot self-heal; the caller must tear it down and rebuild."""
```

Drivers **MUST translate** every transport/hardware fault into this hierarchy.
A raw `serial.SerialException`/`OSError` **MUST NOT** cross the seam.

### 2. Bounded-liveness guarantee on the streaming lifecycle

`stream()` (and `start`/`stop`/`configure`) **MUST** do one of:
- keep yielding frames, or
- **self-heal transparently** (internal `reset -> init -> start`) and resume, or
- raise `FatalInstrumentError`.

It **MUST NOT** block indefinitely. "Bounded" is **relative to the expected sweep
cadence** (a slow large program has a longer bound than a fast small one), not a
fixed wall-clock constant -- the exact policy (timeout multiple, reset budget,
escalation count) is M34 design, not fixed here.

### 3. Self-healing lives in the driver; `FatalInstrumentError` is the escalation

The driver owns transient recovery (no-data timeout, corruption detection,
bounded `reset/init/start`). When it exhausts its recovery budget it raises
`FatalInstrumentError` -- the single, typed handoff that tells the engine to do
the heavy recovery (teardown + rebuild + re-arm). The engine
(`recorder`/`scheduler`) consumes **only** the contract: frames, or
`FatalInstrumentError`. It stops reaching into transport internals (e.g. calling
`stop()` on a dead port).

`CONTRACT_VERSION` 0.4.0 -> **0.5.0**. This **tightens** implementer obligations
(it is breaking in the sense that a driver which may hang or leak a transport
exception is no longer conformant), so every driver **and its fake** is
re-verified against it -- it is not a silent break.

## Consequences

- **Drivers** (Callisto heterodyne, RX-888 SDR, and every fake) implement
  self-healing + fault translation. The fakes/simulator gain a **fault-injection**
  mode (induce a stall, a corrupt sweep, a hard error) so containment is testable
  with no hardware -- each driver is tested against *"instability stays contained:
  the driver self-heals or raises `FatalInstrumentError`, and never hangs."*
- **The engine simplifies.** `acquisition`/`recorder`/`scheduler` lose ad-hoc
  fault handling and gain one clear path: stream frames; on `FatalInstrumentError`
  rebuild and re-arm; reconcile liveness via a `last_frame_at` timestamp.
- **Watchdog moves and changes shape.** The high-bit corruption test moves
  **before** `to_8bit` (into the driver/parser, where the raw value still has its
  high bits) so it can actually fire; the watchdog gains a **silence** dimension.
- **Third parties** get a precise, versioned promise: a conformant driver never
  hangs the host and never leaks its transport's exceptions -- the prerequisite
  for loading closed SDR/FPGA drivers safely.
- **Clock gating (decided).** Resolving the DESIGN §12a vs legacy-P11 tension:
  NG **trusts the boot-synced clock and flags affected sweeps; it does not tear
  down a running recording on drift.** The acquire service is ordered after
  `chrony` (already so in the unit); a drift/loss-of-sync event marks the
  affected frames (a per-sweep clock-quality flag in the recording) rather than
  force-stopping into a new file. This keeps continuity (one file) and pushes the
  judgement to the data, matching how the legacy stayed simple and robust. The
  current force-stop-on-drift behaviour in `scheduler_service` is removed in M34.
- **Deferred to the M34 design (not this ADR):** the no-data timeout policy, the
  reset budget + escalation counts, the per-sweep clock-flag representation, and
  USB re-enumeration/reconnect. This ADR fixes the **seam**; those are tuning
  behind it.

## Note on location

Decided: the `docs/architecture/` subtree **ships** (carved out of the gitignored
`docs/` tree) because plugin-contract ADRs are exactly what third-party driver
authors build against; the rest of `docs/` (planning, research, logs) stays
maintainer-local.
