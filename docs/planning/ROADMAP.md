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
| **M7 — Security & deploy hardening** *(release gate)* | v0.2.1 ✓ done | S021-S023 |
| **M8 — Legacy migration & interop** | v0.2.2 ✓ done | S024-S025 |

Order: M6 (autonomy) → M7 (the blocking gate) → M8 (adoption); version close
merges `0.2-dev` → `main`.

## v0.3 released (M9 SDR + M10 fleet + UI)

`main` is at **v0.3.2**. Both SDR classes (host-DSP + FPGA) record through the
same pipeline as the heterodyne receiver, an observatory aggregates many
stations' health, and the portal surfaces every feature. Tags v0.3.0-v0.3.2.

## v0.4 -- "No orphan users" (SELECTED, not started)

Theme: **feature parity with the legacy Windows (Borland) suite** so the
heterodyne stations already in the field migrate without losing functionality.
Driven by `legacy/sources/WINDOWS_FUNCTIONALITY.md`, not abstract design gaps.
Branch `0.4-dev` from `main`.

The recorder *protocol* is already faithful (tuner step, band-select, PLL
dividers, firmware 1.5/1.7/1.8, EEPROM upload, overview command -- all from M0).
The gaps are the *operational behaviors, bench tools, and publication outputs*
around it.

| Milestone | Closes | Plan |
| -- | -- | -- |
| **M11 — Recorder operational parity** | v0.4.0 ✓ done | S030-S031 |
| **M12 — Bench & diagnostic tools** | v0.4.1 ✓ done | S032-S033 |
| **M13 — Spectrum viewer & publication** | v0.4.2 ✓ done | S034-S035 |
| **M14 — Distribution & generator parity** | v0.4.3 ✓ done | S036-S037 |

Order: M11 (what deployed stations rely on daily) → M12 (commissioning/bench) →
M13 (visualization + public light curves) → M14 (distribution + generator);
version close merges `0.4-dev` → `main`.

Owner decisions (from the milestone-gathering review): burst detection/flagging
(F6) stays **out** -- acquisition-only, analysis lives in doncel. Core license
(ADR-0003) **deferred** until the first public release. GPS/PPS timing (F3) and
the `astro` planning aid remain backlog.

## v0.5 -- "Station completeness" (SELECTED, after v0.4)

Theme: the **design's pillars beyond legacy parity** -- the §8.4 settings depth,
the §14a resilience model, the §15 deployment lifecycle, and the §9 full wizard.
These are the proposed design-gap milestones, **renumbered M15+** and
**de-duplicated against v0.4**: the earlier "Tools & Bench" and "Viewer & data
depth" proposals are already delivered by parity **M12/M13**, and "Analysis" is
dropped per the F6 decision. Branch `0.5-dev` from `main` after the v0.4 close.

| Milestone | Was (design proposal) | Closes | Scope |
| -- | -- | -- | -- |
| **M15 — Station Settings** (§8.4) ✓ done (S038-S039) | M12 | v0.5.0 | users + audit log + config backup/restore + system info (host reboot/log-viewer + data-browser depth -> F12/F13) |
| **M16 — Resilience & supervision** (§14a/§12a) ✓ done (S040-S041) | M14 | v0.5.1 | failure-mode matrix + alert channels + acquisition daemon + drift-gating (cross-process status -> F14) |
| **M17 — Updates & deployment** (§15) ✓ done (S042) | M15 | v0.5.2 | support bundle + update reporting + SD image + config backup/restore (apply/rollback runner -> F15) |
| **M18 — Wizard completeness** (§9) | M16 | v0.5.3 / version close | full multi-step **resumable** wizard, map picker, clone/import branch (F9) |

Folded in: a richer **data browser** (§8.1: calendar/heatmap, in-browser FITS
viewer, bulk download/delete/re-queue) -- the part of the old "Viewer & data
depth" not covered by parity M13 -- rides along in **M15**.

Mapping note: old M11 (Tools & Bench) -> v0.4 **M12**; old M13 (Viewer & dB) ->
v0.4 **M13**; old M17 (Analysis) -> **dropped** (F6 out). The rest shift to M15-M18.

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
