# Feature Backlog — e-Callisto NG

Deferred features and enhancement ideas carry IDs (F1, F2, …) with status,
origin, and motivation.

## Open

_None — all open items are promoted to v0.7 milestones (below)._

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
