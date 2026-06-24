# Sprint 0.1-M0-S004 -- end-to-end record loop + CLI (M0 close)

**Status:** Completed (2026-06-25)
**Date:** 2026-06-25
**Branch:** ``0.1-dev``

## Goal

Run a recording from driver to FITS on disk with one command, hardware-free
(fake) and over real serial (Callisto), closing M0.

## Goal Met?

**Yes.** `ecallisto-ng record` drives an instrument end-to-end and writes a
standard FITS; verified for both the fake driver and the Callisto simulator. M0
completion criterion met; tagged v0.1.0.

## Actions Taken

- **D1 B1 fix.** `CallistoDriver.configure` now takes sweeps/sec; the clock
  divider is computed from pixels/sec = sweeps x channels. Test asserts the FITS
  time axis (CDELT1) = 1/sweeps-per-second on the Callisto path. B1 -> Resolved.
- **D2 `services/acquisition.py`.** `record()` -- connect/identify/configure/
  start, collect `max_frames` via `islice(stream)`, stop/close in `finally`,
  assemble a `Recording`, hand to the writer. Speaks only contracts.
- **D3 `connections/serial_link.py`.** `SerialConnection` over pyserial
  (lazy-imported; fake/sim path and tests need no serial). `pyserial` added to
  deps.
- **D4 CLI.** `cli.py` `record` subcommand (--driver fake|callisto, --port,
  --instrument, --channels, --frames, --sweep-rate, --focus, --out); entry point
  `ecallisto-ng = ecallisto_ng.cli:main`.
- **D5 tests + close.** `test_acquisition.py` (fake + Callisto-sim -> FITS),
  `test_cli.py` (fake records + prints path; callisto requires --port). SNR
  sweep (vulture) clean. Version 0.1.0, changelog, this logbook.

## Verification

Full gate green: vulture, black-79, ruff, flake8, mypy (30 files), pytest
(**30 passed**) in `.venv` (astropy 8.0). `core` still imports nothing concrete;
pyserial lazy (not needed for tests).

## Milestone M0 -- complete

All M0 sprints (S001-S004) logged Completed. Criterion met: a recording runs
end-to-end (driver -> FITS) via CLI, gate green, contracts in ADRs. Version
bumped to v0.1.0; tag `v0.1.0`; branch `0.1-dev` pushed. (Merge to `main`
happens at v0.1 *version* close, after the remaining milestones.)

## Lessons / Observations

- The acquisition loop touching only contracts (no driver/writer internals) is
  the payoff of the M0 seam work: it records from fake or Callisto unchanged, and
  SDR drivers will drop in the same way.
- Next milestone M1 (backend + portal + auth + wizard) introduces async +
  persistence; the synchronous `record()` stays as the batch/CLI path.

## Tag

``v0.1.0`` at the M0-complete commit on ``0.1-dev``.
