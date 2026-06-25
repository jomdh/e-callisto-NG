# Sprint 0.4-M12-S033 -- noise figure + Tools UI (M12 close)

**Goal:** Y-factor noise figure / slope / bandpass + the Tools bench page.
**Full ID:** 0.4-M12-S033  **Milestone:** M12 (final)  **Branch:** `0.4-dev`  **Status:** Completed.

## Deliverables
- `services/noise_figure.py` (pure: detector_slope, noise_figure, bandpass, stats).
- `POST .../bench/noise_figure` (runs cold/warm/hot sweeps + computes).
- `/portal/tools` page + `tools.js` (detector gauge + NF run) + nav link.

## Acceptance
- [x] NF/slope/bandpass math matches the legacy formulas (pure tests).
- [x] NF endpoint returns freqs/nf/slope/bandpass + mean/sigma.
- [x] Tools page renders; gate green; M12 tagged v0.4.1.
