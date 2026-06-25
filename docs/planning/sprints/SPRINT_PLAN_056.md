# Sprint 0.8-M26-S056 -- FITS output accuracy (M26 close)

**Goal:** Byte-exact FITS fixes (PARITY_AUDIT A3/A6/A7). Closes M26.
**Full ID:** 0.8-M26-S056  **Milestone:** M26 (final)  **Branch:** `0.8-dev`  **Status:** Completed.

## Deliverables
- A3 legacy BUNIT strings (`45*log(sfu+10)`/`40*log(Tant)`) in LegacyFitsWriter;
  A6 binary-table TSCAL/TZERO + D8.3 display cards; A7 DATAMIN/DATAMAX over the
  written (calibrated) image. Factored `_bunit`/`_build_table` hooks.

## Acceptance
- [x] Legacy writer BUNIT + table cards; standard writer unchanged; DATAMIN over
      image. Gate green; M26 -> v0.8.1.
