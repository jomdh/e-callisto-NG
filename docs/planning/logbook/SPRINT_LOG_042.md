# Sprint 0.5-M17-S042 -- support bundle + updates + SD image (M17 close)

**Status:** Completed (2026-06-25)  **Branch:** `0.5-dev`

## Goal / Met?
Deployment lifecycle. **Met** -- a redacted support bundle, update version/channel
reporting, and an SD-image build recipe (config backup/restore shipped in M15).

## Actions
- `services/support_bundle.py` build_support_bundle (zip of version/system/config/
  audit; upload passwords + DDNS/relay redacted; secret_key never included);
  `/api/v1/system/support-bundle` (admin) + settings download button.
- `services/updates.py` parse_version/is_newer/update_info; `/api/v1/system/update`;
  `update_channel` setting.
- `scripts/build-sd-image.sh` (pi-gen stage installing the .deb + enabling both
  services).

## Verification
Gate green: vulture/black/ruff/flake8/mypy (136 files)/pytest (**174 passed**).

## Milestone M17 -- complete
S042. Deployment: config backup/restore (M15) + support bundle + update reporting
+ SD image. The apply/rollback *runner* (needs a real repo + least-priv host hook)
is deferred to F15. Version -> v0.5.2; tag.

## Lessons
- Redacting at export time (not at storage) keeps secrets in the DB encrypted yet
  guarantees the shareable bundle is clean -- asserted in tests.

## Tag
`v0.5.2` at the M17-complete commit on `0.5-dev`.
