# Sprint 0.2-M6-S020 -- calibration wiring + light curves (M6 close)

**Sprint Goal:** An instrument assigned a calibration writes SFU/Kelvin FITS, and
flagged channels produce light-curve files. Closes M6.

**Full ID:** 0.2-M6-S020  **Milestone:** M6 (final)  **Branch:** ``0.2-dev``  **Status:** Planned.

## Deliverables (5)

| # | Task | Layer | Notes |
| -- | -- | -- | -- |
| D1 | `CalibrationSet` model + `Instrument.unit`/`calibration_set_id`; calibration CRUD | api | coefficient sets |
| D2 | thread `unit`+`calibration` through `record()` + `recorder.start` | services | + `calibration_build.resolve` (raw unless calibrated) |
| D3 | wire record route + scheduler `_start` to apply the instrument's calibration | api/services | -- |
| D4 | `services/lightcurve.py` write_light_curves; called in `record()` | services | CSV for flagged channels; none -> no file |
| D5 | tests + milestone close | tests/docs | calibrated FITS via API; LC written/omitted; v0.2.0 |

## Acceptance Criteria

- [ ] An instrument with unit=sfu + a calibration set writes BUNIT=sfu FITS.
- [ ] Raw stays the default when no calibration assigned.
- [ ] Flagged channels produce a light-curve CSV; none flagged -> no file.
- [ ] Gate green; SNR clean; M6 tagged v0.2.0.

## Out of Scope

Calibration UI; dB view; per-channel LC selection UI (refinement).
