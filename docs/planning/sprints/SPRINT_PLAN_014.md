# Sprint 0.1-M4-S014 -- upload transports + uploader + targets

**Sprint Goal:** Send recorded files to a configured destination, once each,
gzipped, without re-sending.

**Full ID:** 0.1-M4-S014  **Milestone:** M4  **Branch:** ``0.1-dev``  **Status:** Planned.

## Decision

`UploadTransport` plugins: `local` (copy/mirror, fully testable reference) and
`ftp` (stdlib, lazy). The uploader gzips then puts via tmp-then-rename and records
an `UploadJob` so files aren't re-sent. Dispatch modes are stored on the target;
this sprint wires manual `run`; immediate/scheduled auto-trigger is refinement.

## Deliverables (5)

| # | Task | Layer | Notes |
| -- | -- | -- | -- |
| D1 | `transports/local.py` + `transports/ftp.py` | transports | UploadTransport impls |
| D2 | `UploadTarget` + `UploadJob` models | api | protocol/host/creds/dispatch/gzip |
| D3 | `services/uploader.py` | services | gzip + put + verify; remote naming |
| D4 | `routes/upload.py` | api | targets CRUD + /run + /queue |
| D5 | tests + logbook | tests | local conforms; gzip; run uploads then skips |

## Acceptance Criteria

- [ ] LocalTransport satisfies the contract; gzip round-trips.
- [ ] Run uploads pending files once; re-run uploads nothing; queue shows done.
- [ ] Gate green.

## Out of Scope

SFTP; credential encryption (B2); immediate/scheduled auto-dispatch; retention.
