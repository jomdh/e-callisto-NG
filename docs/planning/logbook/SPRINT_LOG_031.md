# Sprint 0.4-M11-S031 -- scheduler modes + overview output (M11 close)

**Status:** Completed (2026-06-25)  **Branch:** ``0.4-dev``

## Goal / Met?

Scheduler mode parity + overview output. **Met** -- the scheduler now switches
frequency programs and triggers scheduled overviews; on-demand overview writes
the legacy OVS file pair.

## Actions Taken

- **D3** `services/overview.py` -- `write_overview` (pure, `OVS_<inst>_<ts>.prn`
  + `.csv`, `freq;amp`/`freq,amp`) + `run_overview` (one driver sweep);
  `POST /api/v1/instruments/{id}/overview` (409 while recording).
- **D2a** `Schedule.program_id`; `_channels()` builds channels from the
  program's frequencies + `light_curve_indices_json` -- this also wires the
  per-channel light-curve flag from the program (the D4 remainder).
- **D2b** `Schedule.overview_at` + `last_overview_date`; `_maybe_overview()`
  fires once/day at the time when not recording.
- `FrequencyProgram.light_curve_indices_json` + API fields; console UI gains the
  overview action, schedule program/overview fields, and program LC indices
  (blank number fields now omitted so server defaults apply).

## Verification

Gate green: vulture/black/ruff/flake8/mypy (112 files)/pytest (**123 passed**).

## Milestone M11 -- complete

S030-S031. The recorder now has the legacy day-to-day behaviours fielded
stations rely on: data-loss watchdog (degrade-don't-die) + legacy light-curve
files (S030); program-switch + scheduled/on-demand overview with OVS output
(S031). Version -> v0.4.0; tag v0.4.0.

## Lessons

- Routing the light-curve flag through the *program* (not the instrument) matches
  the legacy frq-file model exactly and made the D4 "flag carried from program"
  fall out of the program-switch wiring -- one change, two deliverables.

## Tag

``v0.4.0`` at the M11-complete commit on ``0.4-dev``.
