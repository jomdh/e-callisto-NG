# Sprint 0.4-M11-S031 -- scheduler modes + overview output (M11 close)

**Sprint Goal:** Legacy scheduler.cfg mode parity (program-switch + scheduled
overview) and the on-demand spectral-overview output. Closes M11.

**Full ID:** 0.4-M11-S031  **Milestone:** M11 (final)  **Branch:** ``0.4-dev``  **Status:** Planned.

## Deliverables (D2 + D3 of M11)

| # | Legacy behaviour | Deliverable |
| -- | -- | -- |
| D3 | "Save spectral overview" -> `OVS_*.prn`/`.csv` (freq;amp) | `services/overview.py` (`write_overview` pure + `run_overview`); on-demand `POST /instruments/{id}/overview` |
| D2a | scheduler.cfg frqfile -> program switch | `Schedule.program_id`; scheduler builds channels from the program (carrying the per-channel **light-curve flag** -- closes D4 wiring) |
| D2b | scheduler.cfg mode 8 -> scheduled overview | `Schedule.overview_at` + `last_overview_date`; scheduler triggers an overview once/day when not recording |
| -- | program light-curve flag (`,>0`) | `FrequencyProgram.light_curve_indices_json` + API |
| -- | console UI | overview action; schedule program/overview fields; program LC indices |

## Acceptance Criteria

- [x] `run_overview` writes the OVS .prn/.csv pair from one driver sweep.
- [x] A schedule's program drives the recorded channels + light-curve flags.
- [x] A scheduled overview fires once per day at `overview_at`, not while recording.
- [x] Gate green; SNR clean; M11 tagged v0.4.0.

## Out of Scope

Bench tools (M12); the public LC PNG / viewer (M13).
