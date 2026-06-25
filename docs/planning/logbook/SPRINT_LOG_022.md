# Sprint 0.2-M7-S022 -- remote-access modes + dynamic DNS

**Status:** Completed (2026-06-25)  **Branch:** ``0.2-dev``

## Goal / Met?

Choose how the station is reached and generate the matching config. **Met** --
`AccessSettings` (lan/public/tunnel), a pure Caddyfile generator per mode, a DDNS
URL builder, and an admin settings + caddyfile API.

## Actions Taken

- **D1** `AccessSettings` singleton model (mode, hostname, tls_email,
  ddns_update_url, tunnel_relay).
- **D2** `services/caddy.py` `build_caddyfile` -- `lan` (`tls internal`),
  `public` (hostname + Let's Encrypt email), `tunnel` (documented stub).
- **D3** `services/ddns.py` `build_update_url({ip})` (pure) +
  `current_public_ip`/`update` HTTP wrappers (uncovered, env-dependent).
- **D4** `routes/access.py` GET/PUT settings (viewer/admin) + GET `/caddyfile`.
- **D5** tests -- caddyfile per mode + validation, DDNS url, settings API + RBAC.

## Verification

Gate green: vulture/black/ruff/flake8/mypy (89 files)/pytest (**83 passed**).

## Lessons

- Keeping the config *generation* pure and tested while leaving the *running* of
  Caddy/DDNS/tunnel to the installer + runbook keeps this CI-testable and matches
  reality (those are host-level concerns).

## Tag

None (M7 closes at S023).
