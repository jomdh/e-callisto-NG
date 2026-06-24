# Sprint 0.1-M5-S017 -- diagnostics + packaging (M5 close, v0.1 release)

**Sprint Goal:** Probe an instrument from the API and install the suite on a
station. Closes M5 and the v0.1 version (merge to main).

**Full ID:** 0.1-M5-S017  **Milestone:** M5 (final)  **Branch:** ``0.1-dev``  **Status:** Planned.

## Decision

A diagnostics endpoint probes the device through the driver (connect/identify/
capabilities) -- hardware-free with the fake driver, real over serial. Packaging
ships a systemd unit (uvicorn app factory) + install script now; the full `.deb`
recipe is outlined for a later sprint.

## Deliverables (5)

| # | Task | Layer | Notes |
| -- | -- | -- | -- |
| D1 | `/instruments/{id}/diagnose` | api | connect/identify/capabilities |
| D2 | `packaging/systemd/ecallisto-web.service` + `scripts/install.sh` | packaging | uvicorn --factory; user/dirs/unit |
| D3 | `packaging/README.md` | docs | layout, systemd, install, .deb plan |
| D4 | tests | tests | diagnose probes fake; packaging artifacts present |
| D5 | version close | docs/git | SNR sweep; v0.1.5; changelog; tag; merge to main |

## Acceptance Criteria

- [ ] Diagnose returns model/firmware/capabilities (fake -> FAKE/8-bit).
- [ ] systemd unit + install script present and valid.
- [ ] SNR sweep clean; gate green; v0.1.5 tagged; 0.1-dev merged to main.

## Out of Scope

Full `.deb` build; SD image; real chrony probe; bench-tool UI (noise figure).
