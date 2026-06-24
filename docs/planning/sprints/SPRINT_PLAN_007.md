# Sprint 0.1-M1-S007 -- instruments: model, CRUD, record control

**Sprint Goal:** Register instruments and start/stop a recording on one via the
API, with the file landing on disk.

**Full ID:** 0.1-M1-S007  **Milestone:** M1  **Branch:** ``0.1-dev``  **Status:** Planned.

## Decision

`Station` (single row -- this host, with its observatory + coordinates) and
`Instrument` rows (station-scoped). A `RecorderService` runs `record()` on a
background thread per instrument; `stop()` calls the driver's `stop()`, which
ends the stream and writes the partial FITS. Hardware-free by default (fake
driver); a serial `address` selects the Callisto driver. True continuous +
live-streamed recording is M2; this is start -> bounded record -> file + status.

## Deliverables (5)

| # | Task | Layer | Notes |
| -- | -- | -- | -- |
| D1 | `Station`, `Instrument` models | api | station-scoped instruments; class/focus/gain/address/enabled |
| D2 | `services/recorder.py` | services | per-instrument threaded recorder + driver factory (fake/callisto) |
| D3 | `api/routes/instruments.py` CRUD | api | list/create/get/patch/delete (viewer reads, operator writes) |
| D4 | record/stop/status endpoints | api | POST /{id}/record, /{id}/stop, GET /{id}/status |
| D5 | tests + logbook | tests | CRUD + RBAC; record -> IDLE with a file; stop |

## Acceptance Criteria

- [ ] Operator creates an instrument; viewer can list but not create (403).
- [ ] POST /{id}/record (fake) reaches IDLE with a FITS file recorded.
- [ ] POST /{id}/stop interrupts a running recording.
- [ ] Gate green; tests pass.

## Out of Scope

Live WebSocket streaming, scheduler-driven start/stop (M2/M3); portal UI (S008).
