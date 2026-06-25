# Sprint 0.8-M25-S054 -- per-instrument device console

**Status:** Completed (2026-06-25)  **Branch:** `0.8-dev`

## Goal / Met?
Per-instrument, class-gated device console. **Met** -- each instrument has a
detail page exposing its functions; e-Callisto (heterodyne) shows the full
toolset (operate + bench detector + noise figure + reconnect), SDR shows the
applicable subset.

## Actions
- `instrument_capabilities` endpoint (builds the driver, checks `BenchCapable` +
  `supports_overview`) -> authoritative per-class capability.
- `/portal/instruments/{id}` (server-side bench gate via build_driver +
  isinstance) + instrument_detail.html (operate / bench / NF / configure) +
  instrument.js (actions + detector + NF + status chip).
- console gains an "open" row action; dashboard card name links to the detail.

## Verification
Gate green: vulture/black/ruff/flake8/mypy (152 files)/pytest (**220 passed**).

## Milestone M25 -- complete
S054. The device-management functions now live inside each instrument's entry,
class-gated -- exclusive Callisto toolset for heterodyne, subset for SDR. The
accuracy/fidelity fixes (M26-M30) land into this view next. v0.8.0; tag.

## Lessons
- Building the driver + `isinstance(.., BenchCapable)` is the single source of
  truth for "what can this instrument do" -- the UI gate and the API gate share it.

## Tag
`v0.8.0` at the M25-complete commit on `0.8-dev`.
