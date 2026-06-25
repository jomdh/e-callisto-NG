# Security policy

## Reporting

Report vulnerabilities privately to the maintainers (see the project homepage);
do not open a public issue for an unfixed vulnerability. We aim to acknowledge
within a few days.

## Hardening already in place

- **No default credentials** -- the admin is created in the first-run wizard.
- **Argon2** password hashing; server-side sessions in HttpOnly cookies; RBAC
  (viewer/operator/admin).
- **Credentials encrypted at rest** (Fernet, keyed from `secret_key`); the API
  never returns secrets.
- **Content-Security-Policy** enforced on every response (`script-src` is
  nonce + self; no inline scripts).
- **Append-only audit log** of security-sensitive actions (ADR-0006).
- **Host actions run through a least-privilege hook** (ADR-0008); the web
  process never executes arbitrary commands and is disabled by default.
- **Support bundles redact secrets**; `.env`/`secret_key` are never committed.

## Operator responsibilities

Set a strong `ECALLISTO_SECRET_KEY`, run behind TLS (the Access page generates a
Caddy config), and keep the station updated.
