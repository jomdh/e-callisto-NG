# Sprint 0.4-M14-S036 -- SFTP transport + dated backup archive

**Status:** Completed (2026-06-25)  **Branch:** `0.4-dev`

## Goal / Met?
SFTP + dated archive. **Met** -- `SftpTransport` (paramiko) ships files over SSH
with the tmp-then-rename safety; uploaded files can be moved into a dated
`YYYY/MM/DD` archive (legacy FITbackup) instead of being pruned.

## Actions
- `transports/sftp.py` SftpTransport (lazy SSH connect, put tmp->rename, verify);
  registered `sftp` in build_transport; console protocol option; paramiko dep.
- `uploader_service.archive_file` (pure move into dated tree) + `archive_done`
  (uploaded-everywhere files only); `archive_dir` setting; tick archives-or-prunes.

## Verification
Gate green: vulture/black/ruff/flake8/mypy (122 files)/pytest (**146 passed**).

## Lessons
- archive_done globs `*.fit` directly rather than via the FITS-validating
  catalog, so a partial/odd file still archives once uploaded everywhere.

## Tag
None (M14 closes at S037 with the v0.4 version close).
