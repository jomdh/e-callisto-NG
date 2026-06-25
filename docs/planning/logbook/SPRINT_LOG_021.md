# Sprint 0.2-M7-S021 -- credential encryption (B2) + CSP (release gate)

**Status:** Completed (2026-06-25)  **Branch:** ``0.2-dev``

## Goal / Met?

Close the two blocking security gaps. **Met** -- upload credentials are encrypted
at rest and never returned via the API; every response carries a CSP header and
the only inline script carries the matching nonce. The v0.2 release gate holds.

## Actions Taken

- **D1** `api/crypto.py` -- Fernet key derived from `secret_key`;
  `encrypt`/`decrypt` (empty round-trips to empty).
- **D2** create-target encrypts the password; `build_transport` decrypts at the
  point of use (FTP).
- **D3** `TargetOut` excludes the secret (exposes `has_password`); list + create
  return it -- **B2 resolved**.
- **D4** CSP middleware sets a per-request nonce + `Content-Security-Policy`
  (`script-src 'self' 'nonce-...'`); base template's theme-bootstrap script
  nonced. tests cover crypto round-trip, no-leak, ciphertext-at-rest, CSP+nonce.

## Verification

Gate green: vulture/black/ruff/flake8/mypy (85 files)/pytest (**79 passed**).

## Lessons

- Deriving the Fernet key from `secret_key` makes encryption machine-bound by
  install config, no separate keyfile to manage; production must set a real
  `ECALLISTO_SECRET_KEY` (dev default is clearly insecure).
- Allowing `'unsafe-inline'` for *styles* (templates use inline `style=`
  attributes) while keeping *scripts* strict (nonce only) is the pragmatic CSP
  that doesn't require rewriting every template.

## B2 -> Resolved.

## Tag

None (M7 closes at S023).
