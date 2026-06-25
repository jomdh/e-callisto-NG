# Sprint 0.8-M26-S055 -- protocol accuracy (band/F0/control/firmware)

**Goal:** Byte-exact device-command fixes (PARITY_AUDIT A1/A2/A4/A5).
**Full ID:** 0.8-M26-S055  **Milestone:** M26  **Branch:** `0.8-dev`  **Status:** Completed.

## Deliverables
- A1 `band_for` inclusive `<=` (171/450); A2 `tune_command` `F0%07.3f`
  (zero-pad + 3 decimals); A4 10-bit forces chargepump-on control byte (0xC6);
  A5 `detect_firmware` falls back to a default profile (10-bit/37.70) for
  unrecognized devices instead of rejecting; driver no longer raises.

## Acceptance
- [x] Boundary/format/control/default vectors vs legacy; existing tests updated
      to the corrected values. Gate green; 225 tests.
