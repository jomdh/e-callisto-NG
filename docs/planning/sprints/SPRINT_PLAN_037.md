# Sprint 0.4-M14-S037 -- generator LO/RFI + connection test (M14 + v0.4 close)

**Goal:** GenFrqPrg completeness (LO converter math + RFI-exclusion band) +
upload-target connection test. Closes M14 and the v0.4 version.
**Full ID:** 0.4-M14-S037  **Milestone:** M14 (final)  **Branch:** `0.4-dev`  **Status:** Completed.

## Deliverables
- `freqgen`: `exclude_band` (RFI) in generate_frequencies; `rf_to_if`
  (direct/usb/lsb/up LO math); generate endpoint exclude_from/to.
- `uploader.test_target` + `POST /upload/targets/{id}/test`; console test action.

## Acceptance
- [x] RFI band drops bins / avoids RFI points; rf_to_if matches legacy converters.
- [x] Connection test reports reachability. Gate green; v0.4.3; merge to main.
