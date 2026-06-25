# Sprint 0.8-M27-S057 -- scheduler accuracy (B1/B2/B3)

**Status:** Completed (2026-06-25)  **Branch:** `0.8-dev`

## Goal / Met?
Scheduler-accuracy slice of M27. **Met** (B1 scheduler.cfg fidelity, B2 horizon
trim, B3 sun altitude). B4/B5 (OVS/LC formats) + B6 (SchedulerGeni generator)
remain for S058.

## Actions
- B1: `ScheduleEntry.mode` -> single char + `program` 4th column; lossless
  `parse_scheduler_cfg` (A-Z modes, fprog kept); migrate maps mode 8 ->
  overview_at; `ExportEntry`/`build_scheduler_cfg` emit fprog + overview lines;
  schedules export includes program + overview_at.
- B2: `sun_window(horizon_deg)` trims horizon/15h (=deg*4 min) each side, wired
  from `Station.horizon_deg` in the scheduler service.
- B3: sunrise/sunset cross the standard -0.8333 deg altitude (refraction +
  semidiameter), matching helio.cpp.

## Verification
Updated legacy-mode-as-str tests; +test_scheduler_fidelity (4). Gate green: 232.
