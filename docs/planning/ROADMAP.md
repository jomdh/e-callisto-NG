# Roadmap — e-Callisto NG

Single source of truth for milestone state. Detail lives in milestone plans;
this scans in under a minute. Milestones are seeded from
`e-Callisto-NG-DESIGN.md` section 18.

## In progress

### M1 — Backend + portal + auth + wizard  (IN PROGRESS)

FastAPI app, SQLite persistence, the Jinja portal shell on the shared M3 design
system, login/RBAC, the install wizard, instrument config, and start/stop.

| Sprint | Item | State |
| -- | -- | -- |
| S005 | FastAPI app skeleton + SQLite (SQLModel) + settings + health | next |

Completion criteria: an operator can log in, complete the wizard, register an
instrument, and start/stop a recording from the browser. Closes at a version
bump (v0.1.1).

Sprint plans: `sprints/SPRINT_PLAN_NNN.md`; logbooks: `logbook/SPRINT_LOG_NNN.md`.

## Completed

### M0 — Core contracts + record loop  (v0.1.0, 2026-06-25)

Seams first; the record loop proved them. S001 scaffold+contracts+FakeDriver,
S002 Callisto driver+simulator, S003 standard FITS writer, S004 record loop+CLI.
End-to-end `ecallisto-ng record` → FITS; 30 tests; ADRs 0001-0004.

## Planned

- **M2** — Live & data (WebSocket waterfall island, live viewer, data browser).
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
