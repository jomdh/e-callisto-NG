# Sprint 0.5-M16-S041 -- acquisition process isolation + drift-gating (M16 close)

**Status:** Completed (2026-06-25)  **Branch:** `0.5-dev`

## Goal / Met?
Process isolation + drift. **Met** -- acquisition can run as its own systemd
daemon (`ecallisto-ng acquire`) while the web app runs loop-free; clock drift
beyond a tolerance gates recording.

## Actions
- ADR-0007 (+ index); `run_loops_in_web` setting (default true) + lifespan guard;
  CLI `acquire` daemon; `packaging/systemd/ecallisto-acquire.service`.
- `clock.within_drift` (pure) + `clock_offset_ms` (chronyc, pragma);
  `max_clock_offset_ms` setting; scheduler gate = may_record AND within_drift.

## Verification
Gate green: vulture/black/ruff/flake8/mypy (133 files)/pytest (**170 passed**).

## Milestone M16 -- complete
S040-S041. Resilience model: degrade-don't-die matrix + email/webhook alert
channels (S040); acquisition isolatable as a supervised process + drift-gating
(S041). Version -> v0.5.1; tag.

## Lessons
- Default single-process mode (loops in web) keeps dev/test trivial; isolation is
  one setting + one extra unit. The honest limitation (cross-process status, F14)
  is documented rather than hidden.

## Tag
`v0.5.1` at the M16-complete commit on `0.5-dev`.
