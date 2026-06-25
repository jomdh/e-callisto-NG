# Sprint 0.2-M7-S023 -- NTP clock probe + .deb packaging (M7 close)

**Status:** Completed (2026-06-25)  **Branch:** ``0.2-dev``

## Goal / Met?

Real clock-sync in health + a `.deb`. **Met** -- `clock_synced` probes
`timedatectl` (tri-state), health reflects it, the scheduler gates recording when
sync is required and known-bad, and `packaging/debian/` builds the package.

## Actions Taken

- **D1** `services/clock.py` -- `clock_synced` (timedatectl, None where absent),
  `may_record(require, synced)` gate (blocks only required + known-bad).
- **D2** health route passes `clock_synced()` to `build_report`; scheduler `tick`
  computes the gate and won't start (and will stop) recordings when blocked;
  `require_clock_sync` setting (default off).
- **D3** `packaging/debian/{control,rules,postinst,changelog}` -- venv build +
  `callisto` user + dirs + systemd unit + a generated `secret_key` on install.
- **D4** tests -- clock tri-state, gate truth table, health includes clock,
  debian artifacts present.

## Verification

Gate green: vulture/black/ruff/flake8/mypy (91 files)/pytest (**87 passed**).

## Milestone M7 -- complete (release gate satisfied)

S021-S023 logged. **The v0.2 release gate holds**: credentials encrypted (B2),
CSP enforced (both in S021). Plus remote-access modes + DDNS, real clock probe +
gate, and a `.deb`. Version -> v0.2.1; tag v0.2.1; pushed.

## Lessons

- Tri-state clock sync (True/False/None) + a "block only on known-bad" gate avoids
  the trap of refusing to record on hosts where sync simply can't be probed.

## Tag

``v0.2.1`` at the M7-complete commit on ``0.2-dev``.
