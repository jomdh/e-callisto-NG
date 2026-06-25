# Sprint 0.8-M29-S063 -- bench completeness (M29 close)

**Status:** Completed (2026-06-25)  **Branch:** `0.8-dev`

## Goal / Met?
Bench completeness (audit C). **Met** (C1 already in M26; C3-C7 added; C2
constants defined). 

## Actions
- C3 integration averaging (N reads/point) in read_detector + sweep.
- C4 scalar config gradient option for noise_figure + bandpass (SlopeLike =
  vector | scalar); NF endpoint `gradient` field.
- C5 agc_sweep (PWM -> detector mV) + endpoint.
- C6 scope (time-domain detector capture + trigger threshold) + endpoint.
- C7 relay settle delay (injectable sleep) in sweep + NF endpoint settle_s.
- C2 FORMAT_MV/FORMAT_MHZ_MV protocol constants (full wire integration is a
  hardware-path detail behind BenchCapable).

## Verification
+test_bench_completeness (7). Gate green: **268 passed**.

## Milestone M29 -- complete (v0.8.4)
C1 (M26) + C3-C7 (this sprint) + C2 constants. The scope is the data path +
trigger (not the full live Digitizer UI); C2's wire path needs hardware to
verify. Honest partials noted.
