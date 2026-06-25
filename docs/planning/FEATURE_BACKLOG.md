# Feature Backlog — e-Callisto NG

Deferred features and enhancement ideas carry IDs (F1, F2, …) with status,
origin, and motivation.

## Open

| ID | Feature | Origin | Motivation |
| -- | -- | -- | -- |
| F17 | doncel.dev integration (data + API) | DESIGN §1 | NG and doncel share domain/tech/design system but stay **disconnected for now** (owner, 2026-06-25); integration intended later but **not** via the push/pull API sketched in v0.7 -- approach TBD |

## Promoted to milestones

These were open F-items; milestone-gathering reviews promoted them to planned
milestones (see ROADMAP).

| ID | Feature | Milestone |
| -- | -- | -- |
| F5 | In-app help + support-bundle export | M17 (v0.5) |
| F9 | Full multi-step resumable install wizard | M18 (v0.5) |
| F10 | Acquisition as an isolated supervised process + failure matrix | M16 (v0.5) |
| F11 | Updates (channels/rollback) + config backup/restore + SD image | M17 (v0.5) |
| F13 | Data-browser depth + operations cockpit | M20 (v0.7) |
| F12 | Host ops: reboot/shutdown + journald log viewer | M21 (v0.7) |
| F14 | DB-backed recorder run-state (cross-process status) | M21 (v0.7) |
| F15 | Update apply/rollback runner (host hook) | M21 (v0.7) |
| F3 | GPS/PPS high-accuracy timing add-on | M23 (v0.7) |
| F8 | `astro` planning aid (source az/el vs horizon) | M24 (v0.7) |
| F16 | Interactive offline map picker for coordinates | M24 (v0.7) |

## Closed by owner decision

| ID | Feature | Decision |
| -- | -- | -- |
| F6 | Burst detection / quicklook flagging | **Out of scope** (2026-06-25): suite stays acquisition-only; analysis lives in doncel.dev. |

## Delivered

| ID | Feature | Where |
| -- | -- | -- |
| F1 | SDR class-2 (host-DSP) driver | M9 / v0.3.0 (S026) |
| F2 | SDR class-3 (FPGA) driver + network backend | M9 / v0.3.0 (S027) |
| F4 | Observatory-level fleet view (multi-station) | M10 / v0.3.1 (S028) |
| F7 | Portal UI for all operator features | v0.3.2 (S029) |

## v0.4 parity scope (tracked as milestones, not F-items)

Legacy Windows parity is the v0.4 theme; the specific gaps are enumerated in the
M11-M14 milestone plans (watchdog, scheduler modes, overview output, light-curve
format, bench/NF tools, spectrum viewer, public LC PNG, dB view, SFTP, backup
tree, generator LO/RFI). Source of truth: `legacy/sources/WINDOWS_FUNCTIONALITY.md`.

## F18 — General-purpose band plan (decided 2026-06-25)

Make the suite multi-config, not Callisto-range-bound. Per-instrument
**band plan**: multiple segments (start/stop or center/span + channels,
per-segment resolution/dwell), validated against each driver's declared
`Capabilities.bands_mhz`. Callisto stays fixed 45-870; SDRs/FPGAs declare
their own. Derive channel-gen, overview, freqgen, and FITS axes from the
plan instead of the hardcoded 45-870. **Owner chose the full band-plan
model; scheduled AFTER M28-M30 fidelity.** Needs an ADR (core/contract +
schema change) and ties to the DB-migration gap (Alembic).
