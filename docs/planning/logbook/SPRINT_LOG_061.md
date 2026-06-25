# Sprint 0.8-M28-S061 -- frq-file export + grid snap (M28 D1/D4)

**Status:** Completed (2026-06-25)  **Branch:** `0.8-dev`

## Goal / Met?
The biggest generator gap (audit D1) + grid snap (D4). **Met.** D2 (nonlinear-
start), D3 (LO into generation), D5 (RFI keep-N) remain for S062.

## Actions
- D1: `build_frequency_program_cfg` writes a legacy `frqXXXXX.cfg` -- `[target]`,
  `[on_line_testpoint_number]=N/2`, `[number_of_measurements_per_sweep]=N`,
  `[number_of_sweeps_per_second]=800/N`, `[external_lo]`, and `[NNNN]=FFFF.FFF,lc`
  channel lines with the light-curve flag. `GET /programs/{id}/export/frq`.
- D4: selections snap to the 0.0625 MHz synthesizer grid; even mode records the
  bin edge (not centre); RFI exclusion now checks the final selected frequency
  (robust for both modes).

## Verification
+test_frqfile (4); updated even-mode/exclusion tests to edge+snap. Gate: 258.
