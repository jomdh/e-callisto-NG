# Sprint 0.7-M22-S050 -- timing precision (M22 close)

**Status:** Completed (2026-06-25)  **Branch:** `0.7-dev`

## Goal / Met?
Timing precision (F3). **Met** -- a TimeSource contract with system + GPS
implementations + a fake, a per-class timestamping correction, timing provenance
on recordings, and a Time page.

## Actions
- ADR-0009 + index; `core.contracts.TimeSource` (name/now/offset_ms/locked);
  CONTRACT_VERSION 0.4.0; exported from core.
- `services/timing.py`: SystemTimeSource (OS clock + chrony), GpsTimeSource
  (gpsd/chrony refclock, pragma), FakeTimeSource; `get_time_source`;
  `corrected_timestamp` (heterodyne 20ms / SDR-soft 10ms / FPGA 1ms).
- `RecordingMeta.time_source` + `clock_offset_ms`; record route + scheduler set
  them from the active source; `time_source` setting.
- `GET /api/v1/system/time` + `/portal/time` + time.js + nav link.

## Verification
Gate green: vulture/black/ruff/flake8/mypy (146 files)/pytest (**205 passed**).

## Milestone M22 -- complete
S050. Timing model + GPS path behind a clean contract, fully tested against a
fake; recordings record their time source + offset. Version -> v0.7.2; tag.

## Lessons
- Recording the time source + offset as provenance (like the units level) means
  downstream tools know each product's timing quality without trusting the clock.

## Tag
`v0.7.2` at the M22-complete commit on `0.7-dev`.
