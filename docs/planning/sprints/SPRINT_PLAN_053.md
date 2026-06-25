# Sprint 0.7-M24-S053 -- release readiness (AGPLv3) (M24 + v0.7 close)

**Goal:** Apply AGPLv3 + release hygiene -> v1.0 candidate. Closes M24 and v0.7.
**Full ID:** 0.7-M24-S053  **Milestone:** M24 (final)  **Branch:** `0.7-dev`  **Status:** Completed.

## Deliverables
- `LICENSE` = vendored AGPLv3 (FSF, byte-exact) + `scripts/fetch-license.sh`.
- pyproject `license = "AGPL-3.0-or-later"` (PEP 639; setuptools>=77); SPDX
  header on all 96 source files.
- GOVERNANCE.md (plugin independence + contract semver + DCO), CONTRIBUTING.md
  (DCO), SECURITY.md; README license section.
- Release-hygiene test (license/SPDX/governance/no-.env).

## Acceptance
- [x] AGPLv3 + SPDX + governance + DCO; no secrets committed; gate green.
- [x] v0.7.4 (v1.0 candidate); merge 0.7-dev -> main.
