# Sprint 0.7-M22-S050 -- timing precision (TimeSource + correction) (M22 close)

**Goal:** A TimeSource contract (system/GPS), per-class timestamping correction,
timing provenance, and a Time page. Closes M22.
**Full ID:** 0.7-M22-S050  **Milestone:** M22 (final)  **Branch:** `0.7-dev`  **Status:** Completed.

## Deliverables
- ADR-0009; `core.TimeSource` Protocol (CONTRACT_VERSION 0.3.0 -> 0.4.0).
- `services/timing`: System/Gps/Fake sources + `get_time_source` +
  `corrected_timestamp` (per-class latency).
- `RecordingMeta` timing provenance (time_source, clock_offset_ms); recorder +
  scheduler set it; `time_source` setting.
- `/api/v1/system/time` + Time page + nav.

## Acceptance
- [x] Sources conform; correction per class; endpoint + page; recordings carry
      provenance. Gate green; M22 -> v0.7.2.
