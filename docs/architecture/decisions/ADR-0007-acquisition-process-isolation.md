# ADR-0007 -- Acquisition as an isolated, supervised process

**Status:** Accepted  **Date:** 2026-06-25  **Milestone:** M16

## Context

DESIGN 14a: *acquisition is independent of the web app*. A web crash, restart, or
hang must never stop recording, and a recording fault must never take down the
web UI. Until now the scheduler + uploader loops run as daemon threads inside the
FastAPI process, so the two share a fate.

## Decision

Allow acquisition to run as its **own OS process**, supervised by systemd,
separate from the web app:

- A CLI daemon `ecallisto-ng acquire` runs the scheduler + uploader loops and
  nothing else. Packaged as `ecallisto-acquire.service`.
- A setting `run_loops_in_web` (default **true** for the single-process dev/test
  experience). Production sets it **false** on the web service so the loops run
  only in the `acquire` daemon; the web app's lifespan skips `start_loop()`.
- Both processes share the SQLite DB (WAL) as the source of truth.

## Consequences

- The two services fail independently: restarting `ecallisto-web` does not
  interrupt recording, and an acquisition crash is restarted by systemd while the
  UI stays up.
- **Known limitation:** recorder *run-state* (recording / idle / last-file) is
  currently in-process memory. When acquisition runs in the separate daemon, the
  web app cannot see live recorder state for manually-started jobs. Persisting
  recorder state to the DB so both processes share it is tracked as **F14** and
  is the next step to make cross-process status seamless. Scheduled recordings
  are unaffected operationally (the daemon owns them); only the *display* of
  state in the web UI is limited until F14.
- Default single-process mode keeps dev/test simple; isolation is opt-in via
  config + the second unit.
