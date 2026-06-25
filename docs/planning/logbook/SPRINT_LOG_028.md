# Sprint 0.3-M10-S028 -- observatory fleet view (M10 close, v0.3 close)

**Status:** Completed (2026-06-25)  **Branch:** ``0.2-dev`` -> merged to ``main``

## Goal / Met?

Oversee several stations from one view. **Met** -- each station serves a
token-gated fleet-health endpoint; an observatory registers peers and an
aggregate endpoint combines self + every reachable peer.

## Actions Taken

- **D1** `services/health_report.build_station_health(db)`; system route now
  delegates to it (dedup).
- **D2** `PeerStation` model; `fleet_token` setting; `GET /api/v1/fleet/health`
  (token-gated, no session).
- **D3** `services/fleet.gather_fleet(peers, fetch)` (pure, injectable) +
  `default_fetch` (urllib, uncovered).
- **D4** `routes/fleet.py` -- peer CRUD (admin) + `GET /api/v1/fleet` (self +
  peers).
- **D5** tests -- gather with stub fetch (skip disabled / mark unreachable),
  token gate (403 without/with wrong token), peer CRUD + aggregate + RBAC.

## Verification

Gate green: vulture/black/ruff/flake8/mypy (107 files)/pytest (**109 passed**).

## Milestone M10 + v0.3 -- complete

S028 logged. An observatory aggregates multiple stations' health. Version ->
v0.3.1; tag v0.3.1; **0.2-dev merged to main**. v0.3 delivers the SDR classes (M9)
and the fleet layer (M10).

## Lessons

- Injecting `fetch` into `gather_fleet` kept the aggregation pure and testable
  without standing up real peers -- the network call lives only in the default,
  pragma-excluded fetch.
- A token-gated, session-less health endpoint is the clean way to let peers poll
  each other without sharing user credentials.

## Tag

``v0.3.1`` at the M10-complete commit; merged to ``main``.
