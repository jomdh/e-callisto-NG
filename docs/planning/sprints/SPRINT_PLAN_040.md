# Sprint 0.5-M16-S040 -- failure-mode matrix + alert channels

**Goal:** The degrade-don't-die policy matrix + email/webhook alert channels.
**Full ID:** 0.5-M16-S040  **Milestone:** M16  **Branch:** `0.5-dev`  **Status:** Completed.

## Deliverables
- `services/failure_modes.py` (Fault/Response/Policy matrix; should_pause) -- pure.
- `services/alerts.py` AlertChannel protocol + Webhook/Email + dispatch +
  build_channel/enabled_channels; AlertChannelConfig model; SMTP settings.
- `routes/alerts.py` channel CRUD + test; uploader tick dispatches health alerts
  (deduped per change).

## Acceptance
- [x] Matrix responses correct (web-down never pauses); dispatch best-effort.
- [x] Channel CRUD + test; email needs SMTP. Gate green.
