# ADR-0009 — TimeSource contract (system clock vs GPS/PPS)

**Status:** Accepted  **Date:** 2026-06-25  **Milestone:** M22

## Context

DESIGN 12a: continuous NTP resync is paramount, and some stations add a **GPS/PPS**
reference for sub-millisecond absolute timing. Timing is scientific data, so the
station must know *which* time source produced a recording and its offset/lock.

## Decision

Add an optional **`TimeSource`** `Protocol` to `core/contracts.py` (additive,
like `BenchCapable`): `name`, `now()`, `offset_ms()`, `locked()`. Two
implementations -- system clock (offset/lock from chrony) and GPS/PPS (gpsd /
chrony refclock) -- plus a fake. The active source is chosen by the `time_source`
setting; the GPS path is thin and pragma-excluded (no hardware in CI).

A recording records its **timing provenance** -- the source name + offset at
record time -- in `RecordingMeta`, the timing analogue of the units-level
provenance (DESIGN 6b).

Per-class **timestamping correction** (heterodyne serial+sweep latency vs SDR
buffer latency) is a pure, tested function in `services.timing` that shifts the
nominal timestamp by a documented per-class constant.

`CONTRACT_VERSION` 0.3.0 -> **0.4.0** (additive minor bump).

## Consequences

- The whole timing model is tested against a fake TimeSource; real GPS is a thin,
  swappable implementation.
- Recordings carry their time source + offset so downstream tools know the timing
  quality of each product.
- Drift gating (M16) and offset reporting share the same TimeSource.
