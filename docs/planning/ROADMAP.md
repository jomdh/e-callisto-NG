# Roadmap — e-Callisto NG

Single source of truth for milestone state. Detail lives in milestone plans;
this scans in under a minute. Milestones are seeded from
`e-Callisto-NG-DESIGN.md` section 18.

## In progress

### M0 — Core contracts + record loop  (IN PROGRESS)

Define the seams first; the record loop proves them. Getting M0 right is what
makes M1–M5 cheap.

| Sprint | Item | State |
| -- | -- | -- |
| S001 | Scaffold + quality gate + core models + contracts + FakeDriver | done |
| S002 | Callisto serial driver (class-1) + device simulator | done |
| S003 | FITS `OutputWriter` (standard mode) | done |
| S004 | Acquisition service (drive → buffer → write) + CLI + pyserial backend | next |

Completion criteria: a recording runs end-to-end (fake driver → FITS on disk)
via CLI, quality gate green, contracts documented as ADRs. M0 closes at S004
with a version bump to v0.1.0.

Sprint plans: `sprints/SPRINT_PLAN_NNN.md`; logbooks: `logbook/SPRINT_LOG_NNN.md`.

## Planned (post-M0)

- **M1** — Backend + portal + auth + wizard (FastAPI, SQLite, Jinja portal on the
  shared M3 design system, login/RBAC, install wizard, instrument setup).
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
