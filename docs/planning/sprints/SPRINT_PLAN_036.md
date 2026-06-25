# Sprint 0.4-M14-S036 -- SFTP transport + dated backup archive

**Goal:** SFTP upload + the legacy FITbackup dated archive.
**Full ID:** 0.4-M14-S036  **Milestone:** M14  **Branch:** `0.4-dev`  **Status:** Completed.

## Deliverables
- `transports/sftp.py` `SftpTransport` (paramiko, tmp-then-rename); registered
  `sftp` in build_transport; console protocol option; paramiko dep.
- `uploader_service.archive_file` + `archive_done` (move uploaded files into
  `YYYY/MM/DD`); `archive_dir` setting; tick archives when set, else prunes.

## Acceptance
- [x] SftpTransport conforms + builds from an `sftp` target.
- [x] archive_file -> dated tree; archive_done moves uploaded-only, keeps pending.
- [x] Gate green.
