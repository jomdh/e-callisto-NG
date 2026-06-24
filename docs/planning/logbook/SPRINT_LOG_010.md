# Sprint 0.1-M2-S010 -- live frame hub + WebSocket + waterfall island

**Status:** Completed (2026-06-25)  **Branch:** ``0.1-dev``

## Goal / Met?

Stream a recording's spectra live and draw them. **Met** -- a recording's frames
flow recorder -> hub -> WebSocket -> a canvas waterfall; verified by a WS test
that receives JSON frames while a recording runs.

## Actions Taken

- **D1 `services/hub.py`** `FrameHub`: per-instrument fan-out to bounded
  subscriber queues; `publish` drops on a full queue (never blocks the recorder);
  `get_hub` singleton.
- **D2** `record(on_frame=...)` callback; `RecorderService` publishes each frame
  to the hub during the recording thread.
- **D3 `routes/live.py`** -- WebSocket `/ws/live/{id}` (JSON frames, polls the
  queue with a small sleep, cleans up on disconnect) + `GET /portal/live/{id}`.
- **D4** `templates/portal/live.html` + `static/js/waterfall.js` (canvas island:
  scroll-and-paint columns from WS frames; colormap; status).
- **D5 tests** -- hub pub/sub + drop + instrument isolation; WS streams a live
  recording (8-channel frames received).

## Verification

Gate green: vulture/black/ruff/flake8/mypy (54 files)/pytest (**47 passed**).

## Lessons

- Bridging a sync recorder thread to async WS via a thread-safe `queue.Queue` +
  a small async poll is simple and avoids an event-loop-in-thread; bounded queue
  + drop-on-full keeps acquisition isolated from slow clients (DESIGN 11).

## Tag

None (M2 closes at S011).
