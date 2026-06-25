# Sprint 0.2-M7-S022 -- remote-access modes + dynamic DNS

**Sprint Goal:** Let an operator choose how the station is reached -- LAN/VPN,
public HTTPS with dynamic DNS, or an outbound relay tunnel -- and generate the
matching server config.

**Full ID:** 0.2-M7-S022  **Milestone:** M7  **Branch:** ``0.2-dev``  **Status:** Planned.

## Deliverables (5)

| # | Task | Layer | Notes |
| -- | -- | -- | -- |
| D1 | `AccessSettings` model (singleton) | api | mode/hostname/tls_email/ddns/tunnel |
| D2 | `services/caddy.py` build_caddyfile (pure) | services | lan / public+LE / tunnel stub |
| D3 | `services/ddns.py` build_update_url + updater wrapper | services | {ip} template; HTTP call thin/uncovered |
| D4 | `routes/access.py` GET/PUT settings + GET caddyfile (admin) | api | -- |
| D5 | tests + logbook | tests | caddyfile per mode; ddns url; settings API + RBAC |

## Acceptance Criteria

- [ ] Caddyfile differs by mode (lan -> tls internal; public -> hostname + email).
- [ ] DDNS URL substitutes {ip}; missing placeholder errors.
- [ ] Access settings GET (viewer) / PUT (admin); operator PUT -> 403.
- [ ] Gate green; SNR clean.

## Out of Scope

Running Caddy / the DDNS loop / tunnel client (installer/runbook); reachability
probe; access settings UI page.
