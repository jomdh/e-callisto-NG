# Sprint 0.2-M6-S019 -- auto-dispatch uploads + retention

**Status:** Completed (2026-06-25)  **Branch:** ``0.2-dev``

## Goal / Met?

Finished files upload themselves and old ones are pruned. **Met** -- an
`immediate`-dispatch target receives recordings on the uploader tick; retention
deletes files uploaded to all enabled targets and keeps un-uploaded ones.

## Actions Taken

- **D1** Moved upload-pending logic into `services/uploader.upload_pending` +
  `build_transport` (typed against api models -- a bridging orchestration
  service); `/run` route now one line.
- **D2** `UploadTarget.window_start/stop` for scheduled-dispatch windows.
- **D3** `services/uploader_service.py` -- `tick` dispatches per target
  (immediate always / scheduled in-window / manual never); background loop
  (`uploader_tick_seconds`, 0=off) wired into lifespan.
- **D4** `prune` -- deletes files done across all enabled targets and older than
  `retention_days` (<0 = off); never prunes un-uploaded files.
- **D5** tests -- immediate dispatch uploads; retention prunes uploaded-only and
  keeps un-uploaded.

## Verification

Gate green: vulture/black/ruff/flake8/mypy (79 files)/pytest (**73 passed**).

## Lessons

- Modeling auto-dispatch as a *loop that uploads when due* (rather than hooking
  the recorder's finish) kept the recorder ignorant of uploads and made both
  immediate and scheduled fall out of one `tick` -- and reuses the manual `/run`
  path exactly.

## Tag

None (M6 closes at S020).
