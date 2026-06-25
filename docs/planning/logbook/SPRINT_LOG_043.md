# Sprint 0.5-M18-S043 -- multi-step resumable wizard (M18 + v0.5 close)

**Status:** Completed (2026-06-25)  **Branch:** `0.5-dev` -> merged to `main`

## Goal / Met?
Full first-run wizard. **Met** -- a 5-step resumable wizard (admin -> station ->
coordinates -> instrument -> review) persists state across refresh/reboot and
offers a legacy-config import branch.

## Actions
- `WizardState` model (step + accumulated data JSON); `routes/wizard.py`
  rewritten multi-step; admin created only at finalize so `is_configured` gates
  resume correctly.
- Legacy `callisto.cfg` paste on the station step -> parse + pre-fill + jump to
  review (reuses M8 `parse_callisto_cfg`).
- `wizard.html` per-step render with prefilled values, parity sign-convention
  labels, instrument-class select, review summary.

## Verification
Gate green: vulture/black/ruff/flake8/mypy (136 files)/pytest (**176 passed**).

## Milestone M18 + v0.5 -- complete
S043. v0.5 "Station completeness": settings + audit (M15), resilience +
supervision (M16), updates + deployment (M17), wizard (M18). v0.5.3; 0.5-dev ->
main.

## Deferred (honest SNR)
Interactive offline map picker -> F16; labelled numeric lat/lon/alt ship now.

## Tag
`v0.5.3` at the M18-complete commit; merged to `main`.
