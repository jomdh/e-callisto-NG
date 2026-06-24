# Sprint 0.1-M2-S010 -- live frame hub + WebSocket + waterfall island

**Sprint Goal:** Stream a recording's spectra live to the browser and draw them
as a waterfall.

**Full ID:** 0.1-M2-S010  **Milestone:** M2  **Branch:** ``0.1-dev``  **Status:** Planned.

## Decision

A `FrameHub` (in-memory pub/sub, thread-safe `queue.Queue` per subscriber) sits
between the synchronous recorder thread (publisher) and async WebSocket clients
(subscribers). The recorder publishes each frame via an `on_frame` callback added
to `record()`. The waterfall is a Canvas JS island consuming JSON frames -- GPU
work in the browser, per ADR-0001. Slow clients drop frames (bounded queue), never
block acquisition.

## Deliverables (5)

| # | Task | Layer | Notes |
| -- | -- | -- | -- |
| D1 | `services/hub.py` `FrameHub` | services | subscribe/unsubscribe/publish; bounded, drop-on-full |
| D2 | `record(on_frame=...)` + recorder publishes | services | per-frame callback -> hub |
| D3 | `routes/live.py`: WS `/ws/live/{id}` + `GET /portal/live/{id}` | api | JSON frames; live page |
| D4 | `templates/portal/live.html` + `static/js/waterfall.js` | api | canvas waterfall island |
| D5 | tests + logbook | tests | hub pub/sub; WS receives published frames |

## Acceptance Criteria

- [ ] Hub delivers a published frame to a subscriber; full queue drops, no raise.
- [ ] WS `/ws/live/{id}` streams frames as JSON while a recording runs.
- [ ] Live page renders with the waterfall island wired to the WS.
- [ ] Gate green; tests pass.

## Out of Scope

Data browser / quicklooks / download (S011); housekeeping channel; calibration.
