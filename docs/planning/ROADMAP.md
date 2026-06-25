# Roadmap — e-Callisto NG

Single source of truth for milestone state. Detail lives in milestone plans;
this scans in under a minute. Milestones are seeded from
`e-Callisto-NG-DESIGN.md` section 18.

## In progress

## v0.1 released (all selected milestones M0-M5 complete)

`main` is at **v0.1.5**. A station installs, runs the wizard, records real
Callisto data to FITS, streams it live, schedules to the Sun, browses/uploads it,
monitors health, optionally calibrates, and self-diagnoses. 17 sprints, 5 ADRs,
69 tests, tags v0.1.0-v0.1.5.

## v0.2 -- "Real, safe, drop-in" (SELECTED, not started)

Theme: v0.1 built every piece but isn't yet *unattended*, *field-safe*, or a
*drop-in* for existing stations. v0.2 closes those three gaps. Branch `0.2-dev`
from `main`. **Release gate (operator directive): B2 credential encryption and
CSP are blocking -- v0.2 does not ship until both hold.**

| Milestone | Closes | Plan |
| -- | -- | -- |
| **M6 — Autonomous operation** | v0.2.0 ✓ done | S018-S020 |
| **M7 — Security & deploy hardening** *(release gate)* | v0.2.1 | `milestones/V0.2_M7_security.md` (S021-S023) |
| **M8 — Legacy migration & interop** | v0.2.2 / version close | `milestones/V0.2_M8_migration.md` (S024-S025) |

Order: M6 (autonomy) → M7 (the blocking gate) → M8 (adoption); version close
merges `0.2-dev` → `main`.

## Deferred to v0.3+

- **M9** — SDR classes: class-2 host-DSP driver + USB backend (F1), then class-3
  FPGA + network backend (F2) -- the headline extensibility, on the M0 seams.
- **M10** — Observatory/fleet view across multiple stations (F4).
- Bench-tool UI (noise figure), burst detection/flagging (F6), GPS/PPS timing
  (F3), in-app help + support bundle (F5), full multi-step wizard, SD image.

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

### M5 — Calibration & diagnostics + packaging  (v0.1.5, 2026-06-25)

Optional SFU/Kelvin calibration in the writer; device diagnostics endpoint;
systemd + install-script packaging. S016-S017.

## Conventions

Work traces to a milestone. Full sprint/logbook ceremony is adopted once a
delivery cadence exists (see `CLAUDE.md`). Backlogs: `BUG_BACKLOG.md`,
`FEATURE_BACKLOG.md`. Decisions: `../architecture/decisions/ADR_INDEX.md`.
