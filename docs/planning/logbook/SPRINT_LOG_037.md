# Sprint 0.4-M14-S037 -- generator LO/RFI + connection test (M14 + v0.4 close)

**Status:** Completed (2026-06-25)  **Branch:** `0.4-dev` -> merged to `main`

## Goal / Met?
Generator parity + connection test. **Met** -- the generator excludes an RFI
band and exposes the LO converter math; upload targets have a connection test.

## Actions
- `freqgen.generate_frequencies` gains `exclude_band` (drops centred bins, quiet
  mode ignores in-band points); `rf_to_if(rf, lo, converter)` for direct/usb/lsb/
  up; generate endpoint exclude_from/exclude_to.
- `uploader.test_target` (build+connect+close) + `POST /upload/targets/{id}/test`;
  console "test" action.

## Verification
Gate green: vulture/black/ruff/flake8/mypy (123 files)/pytest (**151 passed**).

## Milestone M14 + v0.4 -- complete
S036-S037. Distribution parity (SFTP, dated FITbackup archive, connection test)
and generator parity (LO converter math, RFI-exclusion band). v0.4 "No orphan
users" is released: recorder behaviours (M11), bench tools (M12), viewer +
publication (M13), and distribution + generator (M14). v0.4.3; 0.4-dev -> main.

## Lessons
- Keeping the LO math (`rf_to_if`) as a pure function lets the generator UI and
  the viewer share one source of truth for the converter equations.

## Tag
`v0.4.3` at the M14-complete commit; merged to `main`.
