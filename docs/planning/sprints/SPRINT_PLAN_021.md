# Sprint 0.2-M7-S021 -- credential encryption (B2) + CSP (release gate)

**Sprint Goal:** Close the two blocking security gaps so v0.2 can ship --
encrypt upload credentials at rest and enforce CSP.

**Full ID:** 0.2-M7-S021  **Milestone:** M7  **Branch:** ``0.2-dev``  **Status:** Planned.
**Release gate:** both items are blocking for v0.2 (operator directive).

## Deliverables (4)

| # | Task | Layer | Notes |
| -- | -- | -- | -- |
| D1 | `api/crypto.py` encrypt/decrypt (Fernet from secret_key) | api | secrets at rest |
| D2 | encrypt UploadTarget password on create; decrypt at transport build | api/services | never plaintext in DB |
| D3 | `TargetOut` omits password (has_password flag); list/create return it | api | no leak via API |
| D4 | CSP middleware + nonce; base template inline script nonced; tests | api/tests | script-src self+nonce |

## Acceptance Criteria

- [ ] crypto round-trips; stored password is ciphertext.
- [ ] API never returns the password (only `has_password`).
- [ ] Every response carries a CSP header; the inline script carries the nonce.
- [ ] Gate green; SNR clean.

## Out of Scope

Remote-access modes + DDNS (S022); clock probe + .deb (S023); password rotation.
