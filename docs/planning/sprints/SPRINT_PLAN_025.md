# Sprint 0.2-M8-S025 -- legacy output mode + scheduler.cfg export (M8 + v0.2 close)

**Sprint Goal:** Write archive-compatible legacy-mode FITS and export schedules in
the legacy format. Closes M8 and the v0.2 version (merge to main).

**Full ID:** 0.2-M8-S025  **Milestone:** M8 (final)  **Branch:** ``0.2-dev``  **Status:** Planned.

## Deliverables (5)

| # | Task | Layer | Notes |
| -- | -- | -- | -- |
| D1 | `LegacyFitsWriter` + `get_writer(mode)`; `Instrument.output_mode` | writers/api | legacy adds warning cards |
| D2 | recorder takes a `writer`; route + scheduler pass `get_writer(mode)` | services | per-instrument mode |
| D3 | `legacy_export.build_scheduler_cfg` + `/schedules/export/scheduler.cfg` | services/api | -- |
| D4 | tests | tests | writer modes + legacy comments; scheduler.cfg export |
| D5 | version close | docs/git | v0.2.2; changelog; tag; merge 0.2-dev -> main |

## Acceptance Criteria

- [ ] `get_writer("legacy")` writes the warning COMMENT cards; standard doesn't.
- [ ] Per-instrument output mode drives the writer used for recordings.
- [ ] scheduler.cfg export renders legacy lines.
- [ ] Gate green; SNR clean; v0.2.2 tagged; 0.2-dev merged to main.

## Out of Scope

Custom naming templates; per-upload-target output mode (refinement).
