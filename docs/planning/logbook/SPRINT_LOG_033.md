# Sprint 0.4-M12-S033 -- noise figure + Tools UI (M12 close)

**Status:** Completed (2026-06-25)  **Branch:** `0.4-dev`

## Goal / Met?
NF bench + Tools UI. **Met** -- Y-factor NF / detector slope / bandpass math,
an endpoint that runs the cold/warm/hot sweeps and computes them, and a Tools
page with a detector gauge + NF run.

## Actions
- `services/noise_figure.py` -- detector_slope (|hot-warm|/att), noise_figure
  (Y-factor, NF=ENR-10log10(ylin-0.999)), bandpass (peak-normalized), stats.
- `POST /instruments/{id}/bench/noise_figure` (cold/warm/hot relays from cfg
  defaults 0/3/1).
- `/portal/tools` + `tools.js` (detector gauge 0-2500 mV, NF run summary);
  Tools nav link.

## Verification
Gate green: vulture/black/ruff/flake8/mypy (116 files)/pytest (**135 passed**).

## Milestone M12 -- complete
S032-S033. The commissioning bench is back: detector readout (legacy `simple`),
Y-factor noise figure / slope / bandpass (legacy NF), all behind the BenchCapable
contract and surfaced on a Tools page. Version -> v0.4.1; tag v0.4.1.

## Lessons
- Keeping the NF formulas as pure functions over mV arrays made them exactly
  testable against the legacy math, with the hardware sweep a thin wrapper.

## Tag
`v0.4.1` at the M12-complete commit on `0.4-dev`.
