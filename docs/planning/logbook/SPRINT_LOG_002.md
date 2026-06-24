# Sprint 0.1-M0-S002 -- Callisto serial driver (class-1) + device simulator

**Status:** Completed (2026-06-24)
**Date:** 2026-06-24
**Branch:** ``0.1-dev``  **Commit:** ``8db5119``

## Goal

Make a real Callisto receiver drivable through the `InstrumentDriver`
contract, provable end-to-end with no hardware.

## Goal Met?

**Yes.** `CallistoDriver` runs the full reset->identify->firmware->upload->init
->start->stream->stop lifecycle against `SimulatedCallisto`, yielding normalized
8-bit RAW frames. The legacy protocol is captured as pure, vector-tested
functions.

## Actions Taken

- **D1 `core/connection.py`** -- `Connection` Protocol (write/read/close); the
  device-side seam, distinct from the outbound `UploadTransport`.
- **D2 `drivers/callisto/protocol.py`** -- pure logic from the legacy Linux
  `eeprom.c`/`callisto.c` + Windows `EEPROM.cpp`/`RXRS232.cpp`: `detect_firmware`
  (1.5/1.7/1.8 -> if_init, bit depth, eeprom_info), `divider_bytes`, `band_for`,
  `channel_command` (FE), `init_commands`, `start_commands`, `to_8bit`, framing
  constants.
- **D3 `parser.py`** -- `StreamParser` separating `$...\r` messages from STX-hex
  sweeps, grouping by nchannels, skipping the `0x2323` end marker.
- **D4 `driver.py` + `simulator.py`** -- `CallistoDriver` over `Connection` with
  buffered line/marker reads; `SimulatedCallisto` answers the handshake, acks
  EEPROM writes, streams synthetic hex sweeps between `GE` and `GD`.
- **D5 Tests** -- `test_callisto_protocol.py` (vectors incl.
  `channel_command(0,100MHz,fw1.5)==b"FE1,008,155,198,001\\r"`),
  `test_callisto_driver.py` (firmware detection, end-to-end record, overview,
  parser edge cases).

## Verification

Quality gate green: vulture (whitelist extended for `Connection.read` timeout
param), black-79, flake8, ruff, mypy (18 files), pytest (**20 passed**).
Committed `8db5119` on `0.1-dev` (not yet pushed).

## Lessons / Observations

- The pure-functions-first split made the legacy protocol *verifiable*: known
  command vectors are now regression-locked, where the original lived inside a
  4000-line C++ form.
- The `Connection` seam doubled as the testability seam -- the same simulator
  that enables CI is the design's class-agnostic connection abstraction.
- Deferred deliberately: a real `pyserial` backend and the FITS writer are
  separate sprints (kept this one to 5 deliverables, Rule 6).

## Tag

None (M0 in progress).
