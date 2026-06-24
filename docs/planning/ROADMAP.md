# Roadmap — e-Callisto NG

Single source of truth for milestone state. Detail lives in milestone plans;
this scans in under a minute. Milestones are seeded from
`e-Callisto-NG-DESIGN.md` section 18.

## In progress

### M2 — Live & data  (IN PROGRESS)

Real-time WebSocket waterfall island, live viewer, data browser + quicklooks +
download.

| Sprint | Item | State |
| -- | -- | -- |
| S010 | Live recorder + WebSocket frame hub + waterfall island | next |
| S011 | File catalog + data browser + quicklooks + download | planned |

Completion criteria: an operator watches a live waterfall and browses/downloads
recorded files from the browser. Closes at v0.1.2.

Sprint plans: `sprints/SPRINT_PLAN_NNN.md`; logbooks: `logbook/SPRINT_LOG_NNN.md`.

## Completed

### M0 — Core contracts + record loop  (v0.1.0, 2026-06-25)

Seams first; the record loop proved them. S001-S004. End-to-end
`ecallisto-ng record` → FITS; ADRs 0001-0004.

### M1 — Backend + portal + auth + wizard  (v0.1.1, 2026-06-25)

FastAPI + SQLite, argon2 auth + RBAC + sessions, instrument CRUD + record
control, server-rendered portal on the M3 design system, first-run wizard.
S005-S009.

## Planned

- **M3** — Programs & scheduling (freq-program editor + overview generation,
  sun-relative scheduler).
- **M2** — Live & data (WebSocket waterfall island, live viewer, data browser).
- **M3** — Programs & scheduling (freq-program editor + overview generation,
  sun-relative scheduler).
- **M4** — Distribution & health (uploader, dispatch modes, health/alerts).
- **M5** — Calibration & diagnostics; packaging (.deb + SD image).
- **M6+** — SDR classes (class-2 host-DSP, class-3 FPGA drivers) on the M0 seams.

## Conventions

Work traces to a milestone. Full sprint/logbook ceremony is adopted once a
delivery cadence exists (see `CLAUDE.md`). Backlogs: `BUG_BACKLOG.md`,
`FEATURE_BACKLOG.md`. Decisions: `../architecture/decisions/ADR_INDEX.md`.
