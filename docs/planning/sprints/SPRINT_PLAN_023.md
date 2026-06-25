# Sprint 0.2-M7-S023 -- NTP clock probe + .deb packaging (M7 close)

**Sprint Goal:** Reflect real clock-sync in health (and gate recording on it),
and package the suite as a `.deb`. Closes M7.

**Full ID:** 0.2-M7-S023  **Milestone:** M7 (final)  **Branch:** ``0.2-dev``  **Status:** Planned.

## Deliverables (4)

| # | Task | Layer | Notes |
| -- | -- | -- | -- |
| D1 | `services/clock.py` `clock_synced` (timedatectl) + `may_record` gate | services | tri-state; blocks only when required + known-bad |
| D2 | wire clock into health; scheduler gates recording on it | api/services | `require_clock_sync` setting |
| D3 | `packaging/debian/` (control, rules, postinst, changelog) | packaging | venv + user + unit + secret_key on install |
| D4 | tests + milestone close | tests/docs | clock tri-state + gate + health + debian present; v0.2.1 |

## Acceptance Criteria

- [ ] `clock_synced` returns bool/None and never raises.
- [ ] `may_record` blocks only when sync required and known-bad.
- [ ] Health includes `clock_synced`; scheduler respects the gate.
- [ ] debian/ artifacts present and valid; M7 tagged v0.2.1.

## Out of Scope

Running dpkg-buildpackage in CI; GPS/PPS timing; SD image.
