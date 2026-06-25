# Sprint 0.8-M26-S056 -- FITS output accuracy (M26 close)

**Status:** Completed (2026-06-25)  **Branch:** `0.8-dev`

## Goal / Met?
Byte-exact FITS output (audit A3/A6/A7). **Met.**

## Actions
- Factored `_bunit(unit)` + `_build_table(...)` hooks on StandardFitsWriter.
- A3: LegacyFitsWriter `_bunit` returns the legacy archive strings
  (`45*log(sfu+10)`, `40*log(Tant)`, `digits`) the JavaViewer keys on; the
  standard writer keeps the short `sfu`/`K`.
- A6: LegacyFitsWriter `_build_table` adds TSCAL1/2=1.0, TZERO1/2=0.0 and
  TDISP1/2="D8.3" (the standards-compliant way to carry the legacy 8.3 display
  format -- TFORM itself stays valid FITS).
- A7: DATAMIN/DATAMAX now computed over the written (calibrated) image, not the
  raw frame values -- they differ under SFU/Kelvin.

## Verification
+test_fits_accuracy (3); existing writer tests still pass. Gate green: **228**.

## Milestone M26 -- complete
S055-S056. Device commands (band<=, F0 %07.3f, 10-bit control, firmware default)
and FITS output (legacy BUNIT, table scale/display cards, DATAMIN-over-image) are
now byte-faithful. KEEP items (midnight rollover, ]-ack) left intact. v0.8.1; tag.

## Lessons
- The legacy 8.3 in TFORM is non-standard FITS; expressing it as TDISP keeps the
  file valid while carrying the same display intent -- byte-exact where it counts,
  standards-clean where the original was loose.

## Tag
`v0.8.1` at the M26-complete commit on `0.8-dev`.
