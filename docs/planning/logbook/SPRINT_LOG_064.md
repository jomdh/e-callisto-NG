# Sprint 0.8-M30-S064 -- viewer & publication fidelity (M30 + v0.8 close)

**Status:** Completed (2026-06-25)  **Branch:** `0.8-dev` -> merged to `main`

## Goal / Met?
Last fidelity milestone (audit D6/D7). **Met.**

## Actions
- D6 viewer: OVS-specific mV->dB (/25.4) toggle + unit label (mV/dB) + typed
  Y-axis range zoom (v-ymin/v-ymax), alongside the existing X zoom.
- D7 wwwgeni PNG: SFU clamp [-10,50], ADU->dB (/25.4), y-axis unit label
  ([SFU]/[dB]/[K]), 24-hour UT grid with even-hour labels + dated caption, and
  the legacy publication names Lightcurves<title>.png + dated archive copy.

## Verification
+D6/D7 tests (3); existing renderer test unchanged. Gate green: **271 passed**.

## Milestone M30 + v0.8 -- complete
v0.8 "Heterodyne fidelity & device console": M25 console, M26 recorder/output,
M27 scheduler/files, M28 generator/frq-file, M29 bench, M30 viewer/publication --
plus M31 the real RX-888 SoapySDR driver and hardware discovery. v0.8.5;
0.8-dev -> main.
