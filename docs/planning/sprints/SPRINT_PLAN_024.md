# Sprint 0.2-M8-S024 -- legacy import

**Sprint Goal:** Import an existing Callisto station's config so it comes up in NG
without re-setup.

**Full ID:** 0.2-M8-S024  **Milestone:** M8  **Branch:** ``0.2-dev``  **Status:** Planned.

## Deliverables (4)

| # | Task | Layer | Notes |
| -- | -- | -- | -- |
| D1 | `services/legacy_import.py` parsers | services | callisto.cfg / frq / scheduler / CAL (pure) |
| D2 | `routes/migrate.py` POST /api/v1/import | api | create Station/Instrument/Program/CalibrationSet/Schedule; dry-run |
| D3 | tests | tests | parsers + endpoint creates records + dry-run no-op |
| D4 | logbook | docs | -- |

## Acceptance Criteria

- [ ] Parsers extract identity/coords/program/cal/schedule from legacy text.
- [ ] Import creates the NG records (and assigns the calibration); dry-run no-op.
- [ ] Gate green; SNR clean.

## Out of Scope

In-place FITS indexing (catalog already lists data_dir); wizard import branch UI;
legacy output mode (S025).
