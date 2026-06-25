# Sprint 0.5-M16-S040 -- failure-mode matrix + alert channels

**Status:** Completed (2026-06-25)  **Branch:** `0.5-dev`

## Goal / Met?
Resilience policy + alerts. **Met** -- a pure degrade-don't-die matrix maps each
fault to a response, and health alerts dispatch to email/webhook channels.

## Actions
- `services/failure_modes.py` -- Fault x Response x Policy matrix (disk full ->
  pause, receiver gone -> retry, web down -> continue, ...); `should_pause`.
- `services/alerts.py` -- AlertChannel protocol; WebhookChannel (POST), EmailChannel
  (SMTP), best-effort `dispatch`; `build_channel`/`enabled_channels`.
- AlertChannelConfig model; SMTP settings; `routes/alerts.py` CRUD + test;
  uploader tick computes health alerts and dispatches deduped per change.

## Verification
Gate green: vulture/black/ruff/flake8/mypy (132 files)/pytest (**166 passed**).

## Lessons
- Best-effort dispatch (one bad channel can't block the rest) + per-change dedup
  keeps "always alert" from becoming "always spam".

## Tag
None (M16 closes at S041).
