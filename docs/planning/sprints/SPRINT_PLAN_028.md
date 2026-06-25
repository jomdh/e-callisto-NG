# Sprint 0.3-M10-S028 -- observatory fleet view (M10 close, v0.3 close)

**Sprint Goal:** Let an observatory oversee several stations from one combined
view. Closes M10 and v0.3.

**Full ID:** 0.3-M10-S028  **Milestone:** M10 (final)  **Branch:** ``0.2-dev``  **Status:** Planned.

## Decision

Each station exposes a **token-gated** `/api/v1/fleet/health` (no session, for
peer polling). An observatory registers **peer stations** and an aggregate
endpoint polls each peer's fleet-health and combines it with its own. Aggregation
is pure with an injectable `fetch` so it is testable without the network.

## Deliverables (5)

| # | Task | Layer | Notes |
| -- | -- | -- | -- |
| D1 | shared `build_station_health(db)`; refactor system route to use it | services/api | dedupe |
| D2 | `PeerStation` model + `fleet_token` setting + token-gated `/fleet/health` | api | own health, no session |
| D3 | `services/fleet.py` `gather_fleet(peers, fetch)` (pure) + default urllib fetch | services | injectable |
| D4 | `routes/fleet.py` peer CRUD (admin) + GET `/api/v1/fleet` aggregate | api | self + peers |
| D5 | tests + version close | tests/docs | gather stub; token gate; CRUD/aggregate; v0.3.1; merge to main |

## Acceptance Criteria

- [ ] `/fleet/health` returns health only with the right token (else 403).
- [ ] `gather_fleet` skips disabled peers and marks unreachable ones.
- [ ] Aggregate returns self + peers; peer CRUD is admin-only.
- [ ] Gate green; SNR clean; v0.3.1 tagged; 0.2-dev merged to main.

## Out of Scope

Fleet portal page; cross-station control; peer auth beyond the shared token;
hosted central dashboard.
