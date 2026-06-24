# Sprint 0.1-M5-S016 -- calibration (SFU / Kelvin)

**Sprint Goal:** Optionally turn raw ADC into calibrated SFU or antenna
temperature in the written FITS.

**Full ID:** 0.1-M5-S016  **Milestone:** M5  **Branch:** ``0.1-dev``  **Status:** Planned.

## Decision

Calibration is pure core math (per-channel a/b/cf/Tb, legacy formulas) and opt-in
(DESIGN 6b): a `Recording` carries an optional `Calibration`; the writer applies
it only when a calibrated unit is chosen, else writes raw. Adding an optional
`Recording.calibration` field is backward-compatible (no contract break).

## Deliverables (4)

| # | Task | Layer | Notes |
| -- | -- | -- | -- |
| D1 | `core/calibration.py` | core | ChannelCal/Calibration; to_sfu/to_kelvin (pure) |
| D2 | `Recording.calibration` + writer applies | core/writers | per-channel transform when unit != RAW |
| D3 | export from core | core | Calibration, ChannelCal |
| D4 | tests + logbook | tests | math in range/monotone; raw vs calibrated FITS differ + BUNIT |

## Acceptance Criteria

- [ ] to_sfu/to_kelvin stay in 0..255; higher ADC -> higher value.
- [ ] Calibrated recording writes different pixels + the calibrated BUNIT.
- [ ] Raw remains the default; uncalibrated path unchanged.
- [ ] Gate green.

## Out of Scope

CalibrationSet persistence/UI + wiring into the live recorder (refinement);
dB view.
