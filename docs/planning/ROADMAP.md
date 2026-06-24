# Roadmap — e-Callisto NG

Single source of truth for milestone state. Detail lives in milestone plans;
this scans in under a minute. Milestones are seeded from
`e-Callisto-NG-DESIGN.md` section 18.

## In progress

### M5 — Calibration & diagnostics + packaging  (IN PROGRESS)

Calibration (SFU/Kelvin, optional), diagnostics endpoints, and packaging
(.deb + systemd units).

| Sprint | Item | State |
| -- | -- | -- |
| S016 | Calibration (coefficient sets, SFU/Kelvin in the writer) | next |
| S017 | Diagnostics + packaging (.deb + systemd); version close, merge to main | planned |

Completion criteria: optional calibration produces SFU/Kelvin FITS; the suite
installs via `.deb` with systemd units. Closes v0.1 (merge to main).

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

### M3 — Programs & scheduling  (v0.1.3, 2026-06-25)

Frequency programs (manual + overview-generated quiet-channel selection);
sun-relative scheduler (astropy) with preview. S012-S013.

### M4 — Distribution & health  (v0.1.4, 2026-06-25)

Upload transports (local/FTP) + uploader (gzip, job tracking) + targets;
system health page + alerts. S014-S015.

## Planned

- **M6+** — SDR classes (class-2 host-DSP, class-3 FPGA drivers) on the M0 seams.

## Conventions

Work traces to a milestone. Full sprint/logbook ceremony is adopted once a
delivery cadence exists (see `CLAUDE.md`). Backlogs: `BUG_BACKLOG.md`,
`FEATURE_BACKLOG.md`. Decisions: `../architecture/decisions/ADR_INDEX.md`.
