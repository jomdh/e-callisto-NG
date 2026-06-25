# Bug Backlog — e-Callisto NG

Known bugs carry IDs (B1, B2, …). When fixed, move to Resolved with the
commit hash and date.

## Open

_None._

## Resolved

| ID | Bug | Resolution |
| -- | -- | -- |
| B1 | `sample_rate_hz` semantics inconsistent (pixels/sec vs sweeps/sec). | Fixed in S004 (2026-06-25): `configure` takes sweeps/sec everywhere; Callisto clock divider uses sweeps x nchannels. |
| B2 | Upload credentials stored plaintext. | Fixed in S021 (2026-06-25): Fernet encryption at rest (key from secret_key); API never returns the secret (only has_password). |
