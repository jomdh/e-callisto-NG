# Sprint 0.1-M0-S004 -- end-to-end record loop + CLI (M0 close)

**Sprint Goal:** Run a recording from driver to FITS on disk with one command,
hardware-free (fake) and over real serial (Callisto), closing M0.

**Full ID:** 0.1-M0-S004
**Version:** 0.1  **Milestone:** M0 (final sprint)  **Branch:** ``0.1-dev``
**Status:** Planned.

## Trigger

S002 produces frames, S003 writes FITS. M0's completion criterion is the loop
that joins them, runnable from a CLI. This is the last M0 sprint (SNR sweep +
milestone close per methodology Rules 2-4).

## Decision

A thin synchronous `services/acquisition.record(...)` orchestrates the driver
lifecycle and hands a `Recording` to a writer -- no async, no threads yet (the
web/live layer adds those in M2). Real serial is a `Connection` backend
(`connections/serial.py`, pyserial, lazy-imported) so the fake/sim path needs no
serial dependency. Fix **B1** here: `configure` takes sweeps/sec; the Callisto
clock divider uses pixels/sec = sweeps x nchannels.

## Deliverables (5 -- Rule 6 ok)

| # | Task | Layer | Notes |
| -- | -- | -- | -- |
| D1 | Fix B1: `sample_rate_hz` = sweeps/sec everywhere; Callisto clock uses sweeps x nchannels | drivers | update `CallistoDriver.configure` + tests |
| D2 | `services/acquisition.py` `record()` loop | services | connect->identify->configure->start->stream(N)->stop->close->Recording->write |
| D3 | `connections/serial.py` `SerialConnection` (pyserial, lazy) + dep | connections | implements `Connection`; CLI's callisto path |
| D4 | CLI `record` command + entry point | api/cli | `ecallisto-ng record --driver fake|callisto ...` -> prints FITS path |
| D5 | Tests + SNR sweep + milestone close | tests/docs | acquisition + CLI tests; logbook; resolve B1; bump v0.1.0; changelog; tag |

## Acceptance Criteria

- [ ] `record()` with FakeDriver writes a valid FITS to disk.
- [ ] `record()` with CallistoDriver + SimulatedCallisto writes a valid FITS.
- [ ] CLI `record --driver fake ...` creates the file and prints its path.
- [ ] B1 resolved: Callisto time axis (CDELT1) = 1/sweeps-per-second.
- [ ] `core` still imports nothing concrete; pyserial lazy (not needed for tests).
- [ ] SNR sweep (vulture) clean; full gate green.
- [ ] v0.1.0: pyproject bumped, changelog entry, tag `v0.1.0`, branch pushed.

## Out of Scope

Web/API, async/live streaming, scheduler, uploader, calibration (M1+).

## Tag target

``v0.1.0`` at the M0-complete commit on ``0.1-dev``.
