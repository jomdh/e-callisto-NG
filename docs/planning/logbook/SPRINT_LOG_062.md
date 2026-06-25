# Sprint 0.8-M28-S062 -- generator: nonlinear-start, keep-N, converter (M28 close)

**Status:** Completed (2026-06-25)  **Branch:** `0.8-dev`

## Goal / Met?
Finish M28 (audit D2/D3/D5). **Met.**

## Actions
- D2 `nonlinear_start`: first N channels pinned to start_mhz (legacy nonlin block).
- D5 keep-N RFI: the channel count is preserved by distributing over the band
  minus the excluded width and stepping past the gap (legacy compaction);
  `_excluded` is now half-open so the channel just past the gap is valid.
- D3 converter/LO wired into `/programs/generate` (converter + local_oscillator
  + nonlinear_start). Honours the operator note: a Callisto with an up/down-
  converter has **no RF limit** -- the converter+LO place the chosen band
  wherever needed; generation validates the RF maps through rf_to_if (no clamp).

## Verification
+nonlinear/keep-N/converter tests; updated exclusion tests to keep-N. Gate: 261.

## Milestone M28 -- complete
S061 (frq export + grid snap D1/D4) + S062 (D2/D3/D5). v0.8.3.

## Forward
F18 (full band plan) recorded with the converter note: capability validation on
the IF after conversion, per-segment converter+LO, user-defined config.
