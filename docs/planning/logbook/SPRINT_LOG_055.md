# Sprint 0.8-M26-S055 -- protocol accuracy

**Status:** Completed (2026-06-25)  **Branch:** `0.8-dev`

## Goal / Met?
Byte-exact device commands (audit A1/A2/A4/A5). **Met.**

## Actions
- A1 `band_for` -> `<=` (EEPROM.cpp:259-266): 171.0 -> band 1, 450.0 -> band 2.
- A2 `tune_command` -> `F0%07.3f` (`F0045.000`): zero-pad width 7 + 3 decimals,
  so sub-0.1 MHz NF sweep steps no longer alias (also closes C1).
- A4 `channel_command`: 10-bit tuners force control 0xC6 (chargepump-on)
  regardless of config; 8-bit honors the flag (EEPROM.cpp:249-256).
- A5 `detect_firmware` returns `FIRMWARE_DEFAULT` (10-bit, if_init 37.70) for an
  unrecognized device, matching the legacy default-continue; `identify` no
  longer raises "unsupported firmware".

## Verification
Updated `test_callisto_protocol` (band/firmware) to the corrected legacy values;
new `test_protocol_accuracy`. Gate green: **225 passed**.

## Lessons
- The two failing legacy tests had encoded the *inaccurate* behaviour -- the
  audit was right; correcting the asserts is part of the fix.
