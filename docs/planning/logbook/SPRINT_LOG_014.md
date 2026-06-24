# Sprint 0.1-M4-S014 -- upload transports + uploader + targets

**Status:** Completed (2026-06-25)  **Branch:** ``0.1-dev``

## Goal / Met?

Send recorded files to a destination, once each, gzipped. **Met** -- a recorded
FITS gzips and lands in a local mirror via the uploader; an `UploadJob` prevents
re-sending; a second run uploads nothing.

## Actions Taken

- **D1 transports.** `transports/local.py` `LocalTransport` (copy + tmp-then-
  rename, verify by size) and `transports/ftp.py` `FtpTransport` (stdlib ftplib,
  lazy connect, STOR-tmp-then-rename).
- **D2 models.** `UploadTarget` (protocol/host/base_path/creds/dispatch/gzip),
  `UploadJob` (file/target/state).
- **D3 `services/uploader.py`** -- `upload_file` (gzip to temp -> put -> verify),
  `remote_name_for`.
- **D4 `routes/upload.py`** -- targets CRUD, `/queue`, `/targets/{id}/run`
  (uploads pending, records jobs, skips done).
- **D5 tests** -- local conforms; gzip round-trip; run uploads then skips; queue.

## Verification

Gate green: vulture/black/ruff/flake8/mypy (69 files)/pytest (**61 passed**).

## Lessons

- Filed **B2**: upload credentials are stored plaintext; DESIGN 10 wants
  encryption at rest -- schedule before any real-deployment.
- The transport contract paid off again: `local` is the testable reference and a
  real feature (mirror to a mount); `ftp` is the same shape with no test server.

## Tag

None (M4 closes at S015).
