# Feature Backlog — e-Callisto NG

Deferred features and enhancement ideas carry IDs (F1, F2, …) with status,
origin, and motivation.

## Open

| ID | Feature | Origin | Motivation |
| -- | -- | -- | -- |
| F3 | GPS/PPS high-accuracy timing add-on | DESIGN 12a | sub-ms absolute timing |
| F5 | In-app help + support-bundle export | gap review | replace legacy TeamViewer step |
| F8 | `astro` planning aid (source az/el vs horizon) | WINDOWS_FUNCTIONALITY §2 | observation planning; legacy parity (low priority) |
| F9 | Full multi-step resumable install wizard (map picker, clone/import branch) | DESIGN 9 | smoother first-run; current wizard is minimal |
| F10 | Acquisition as an isolated supervised process + failure-mode matrix | DESIGN 14a | never-lose-data robustness beyond the M11 watchdog |
| F11 | Updates (channels/rollback) + config backup/restore + SD image | DESIGN 15 | field deployment lifecycle |

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
