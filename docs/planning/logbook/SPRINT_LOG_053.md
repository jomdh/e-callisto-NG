# Sprint 0.7-M24-S053 -- release readiness (AGPLv3) (M24 + v0.7 close)

**Status:** Completed (2026-06-25)  **Branch:** `0.7-dev` -> merged to `main`

## Goal / Met?
Make the suite publicly releasable. **Met** -- AGPLv3 applied end to end, plugin
governance + DCO documented, release hygiene verified; tagged a v1.0 candidate.

## Actions
- `LICENSE`: vendored the canonical GNU AGPL-3.0 text from the FSF (byte-exact,
  not transcribed) + `scripts/fetch-license.sh` for reproducibility.
- `pyproject` `license = "AGPL-3.0-or-later"` (PEP 639; build req setuptools>=77);
  SPDX header prepended to every source file (96).
- GOVERNANCE.md (AGPL core + closed-source-plugin allowance via the process +
  versioned-contract boundary; semver contract policy; DCO), CONTRIBUTING.md
  (DCO sign-off), SECURITY.md (reporting + the hardening already shipped);
  README License section.
- `test_release.py`: LICENSE is AGPLv3, pyproject metadata, SPDX on all source,
  governance docs present, no tracked `.env`.

## Verification
Gate green: vulture/black/ruff/flake8/mypy/pytest (**216 passed**). Secret scan
clean; no `.env`/secret files tracked.

## Milestone M24 + v0.7 -- complete
S053. v0.7 "Finish & release": operations cockpit + data depth (M20), host
control & lifecycle (M21), timing precision (M22), planning aids (M23), and
AGPLv3 release readiness (M24). **v0.7.4 = v1.0 candidate**; 0.7-dev -> main.

## Lessons
- Vendoring the license text from the authoritative source (not transcribing it)
  is the responsible way to handle legal text; the fetch script keeps it
  reproducible and byte-exact.
- The AGPL-core / closed-plugin coexistence is exactly why the M0 boundary is a
  process + a versioned contract -- the license decision validated the
  architecture, not the other way around.

## Tag
`v0.7.4` (v1.0 candidate) at the M24-complete commit; merged to `main`.
