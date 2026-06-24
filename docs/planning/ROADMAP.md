# Roadmap — e-Callisto NG

Single source of truth for milestone state. Detail lives in milestone plans;
this scans in under a minute. Milestones are seeded from
`e-Callisto-NG-DESIGN.md` section 18.

## In progress

### M3 — Programs & scheduling  (IN PROGRESS)

Frequency-program editor + overview-based generation; sun-relative scheduler.

| Sprint | Item | State |
| -- | -- | -- |
| S012 | Frequency programs (model, CRUD, overview-based generation) | next |
| S013 | Sun-relative scheduler (astropy ephemeris) + schedule model | planned |

Completion criteria: an operator defines a frequency program and a sun-relative
schedule that drives recording. Closes at v0.1.3.

Sprint plans: `sprints/SPRINT_PLAN_NNN.md`; logbooks: `logbook/SPRINT_LOG_NNN.md`.

## Completed

### M0 — Core contracts + record loop  (v0.1.0, 2026-06-25)

Seams first; the record loop proved them. S001-S004. End-to-end
`ecallisto-ng record` → FITS; ADRs 0001-0004.

### M1 — Backend + portal + auth + wizard  (v0.1.1, 2026-06-25)

FastAPI + SQLite, argon2 auth + RBAC + sessions, instrument CRUD + record
control, server-rendered portal on the M3 design system, first-run wizard.
S005-S009.

### M2 — Live & data  (v0.1.2, 2026-06-25)

Live WebSocket waterfall island; data browser with quicklooks + download.
S010-S011.

## Planned

- **M4** — Distribution & health (uploader, dispatch modes, health/alerts).
- **M5** — Calibration & diagnostics; packaging (.deb + SD image).
- **M6+** — SDR classes (class-2 host-DSP, class-3 FPGA drivers) on the M0 seams.

## Conventions

Work traces to a milestone. Full sprint/logbook ceremony is adopted once a
delivery cadence exists (see `CLAUDE.md`). Backlogs: `BUG_BACKLOG.md`,
`FEATURE_BACKLOG.md`. Decisions: `../architecture/decisions/ADR_INDEX.md`.
