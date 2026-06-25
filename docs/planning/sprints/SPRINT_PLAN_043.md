# Sprint 0.5-M18-S043 -- multi-step resumable wizard (M18 + v0.5 close)

**Goal:** Full multi-step resumable first-run wizard + legacy import branch.
Closes M18 and the v0.5 version.
**Full ID:** 0.5-M18-S043  **Milestone:** M18 (final)  **Branch:** `0.5-dev`  **Status:** Completed.

## Deliverables
- `WizardState` model; multi-step wizard (admin -> station -> coordinates ->
  instrument -> review), resumable; admin created only at finish.
- Legacy `callisto.cfg` paste pre-fills + jumps to review (clone/import branch).
- Parity coordinate labels (sign conventions); class select.

## Acceptance
- [x] Fresh install steps through to dashboard; refresh resumes mid-flow.
- [x] Import branch pre-fills from callisto.cfg. Gate green; v0.5.3; merge to main.

## Deferred
Interactive offline map picker -> F16 (labelled numeric inputs ship now).
