# Sprint 0.8-M27-S060 -- OVS/LC byte-exact + SchedulerGeni (M27 close)

**Status:** Completed (2026-06-25)  **Branch:** `0.8-dev`

## Goal / Met?
Finish M27 file-format fidelity (audit B4/B5/B6). **Met.**

## Actions
- B4 OVS: legacy filename `OVS_<inst>_<title>_<ts>_<FCx>`; header
  `Frequency[MHz];Amplitude RX1[mV] at pwm=<n>;<version>`; `%7.3f;<amp>` rows
  gated to 45-870 MHz and 50<amp<2500; semicolon in the .csv too; route passes
  focus + gain.
- B5 LC: fixed 10 columns (inactive padded 0.000), `Time_UT` label, `%8.4f`/
  `%9.3f` fields, `,<version>,pwm=<n>` header trailer.
- B6: `generate_sun_scheduler_cfg` (sunrise-start / transit-restart / sunset-stop
  / sunset+0.5h overview, quarter-hour snapped, horizon-trimmed) +
  `GET /api/v1/schedules/generate/scheduler.cfg`.

## Verification
Updated OVS/LC tests to the legacy layout; +amplitude-gate +SchedulerGeni tests.
Gate green: **254 passed**.

## Milestone M27 -- complete
S057 (scheduler accuracy B1/B2/B3) + S060 (file formats B4/B5/B6). Scheduler,
OVS, LC, and the sun-derived scheduler.cfg are now byte-faithful. v0.8.2.
