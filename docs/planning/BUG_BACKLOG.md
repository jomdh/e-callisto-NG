# Bug Backlog — e-Callisto NG

Known bugs carry IDs (B1, B2, …). When fixed, move to Resolved with the
commit hash and date.

## Open

| ID | Bug | Found | Notes |
| -- | -- | -- | -- |
| B2 | Upload-target credentials (`UploadTarget.password`) stored in plaintext in SQLite. | S014 | DESIGN 10 requires encryption at rest. Add a machine-bound key + encrypt/decrypt on the credential fields; never return plaintext via the API. Target M4 refinement or M5 hardening. |

## Resolved

| ID | Bug | Resolution |
| -- | -- | -- |
| B1 | `sample_rate_hz` semantics inconsistent (pixels/sec vs sweeps/sec). | Fixed in S004 (2026-06-25): `configure` takes sweeps/sec everywhere; Callisto clock divider uses sweeps x nchannels. Test asserts CDELT1 = 1/sweeps-per-second for the Callisto path. |
