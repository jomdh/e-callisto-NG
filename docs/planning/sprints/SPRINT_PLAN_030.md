# Sprint 0.4-M11-S030 -- data-loss watchdog + light-curve fidelity

**Sprint Goal:** Match two day-to-day legacy behaviours deployed stations rely
on: the data-loss watchdog (auto-stop + alert + auto-restart) and the legacy
light-curve file format.

**Full ID:** 0.4-M11-S030  **Milestone:** M11  **Branch:** ``0.4-dev``  **Status:** Planned.

## Deliverables (2 of M11's 4)

| # | Legacy behaviour | Deliverable |
| -- | -- | -- |
| D1 | data-loss watchdog: high-byte ⇒ auto-stop, `Check RS232-connection!`, auto-restart | `services/watchdog.py` (pure) + wired into `record()` + recorder; corrupt sweep stops early, alerts with verbatim legacy lines; scheduler re-arm = the auto-start |
| D4 | `LCYYYYMMDD_{ADU|SFU}_<title>.txt`, ≤10 channels | rewrite `lightcurve.py`: legacy name + unit tag (ADU/SFU/KEL), 10-channel cap, fractional-UT-hour time column |

## Acceptance Criteria

- [x] Watchdog flags out-of-range sweeps with the exact legacy strings.
- [x] `record()` stops early on data loss, writes the good frames, invokes the
      alert callback; raises if the first sweep is already lost.
- [x] LC file uses the legacy name/format, caps at 10, UT-hours time column.
- [x] Gate green; SNR clean.

## Out of Scope (rest of M11)

Scheduler program-switch + scheduled overview, on-demand overview OVS output
(S031); the program->channel light-curve-flag wiring (S031).
