# Sprint 0.5-M17-S042 -- support bundle + updates + SD image (M17 close)

**Goal:** Support-bundle export, update reporting, SD-image build script.
**Full ID:** 0.5-M17-S042  **Milestone:** M17 (final)  **Branch:** `0.5-dev`  **Status:** Completed.

## Deliverables
- `services/support_bundle.py` (redacted zip: version/system/config/audit) +
  `GET /api/v1/system/support-bundle` (admin) + settings download button.
- `services/updates.py` (version compare) + `GET /api/v1/system/update`;
  update_channel setting.
- `scripts/build-sd-image.sh` (pi-gen + .deb). Config backup/restore: M15.

## Acceptance
- [x] Bundle redacts secrets; update info returns version/channel; SD script present.
- [x] Gate green; M17 tagged v0.5.2.

## Deferred
Update apply/rollback *runner* (host hook + repo) -> F15.
