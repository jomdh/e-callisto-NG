# Sprint 0.2-M8-S025 -- legacy output mode + scheduler.cfg export (M8 + v0.2 close)

**Status:** Completed (2026-06-25)  **Branch:** ``0.2-dev`` -> merged to ``main``

## Goal / Met?

Archive-compatible output + legacy schedule export. **Met** -- `LegacyFitsWriter`
adds the archive's warning cards; `get_writer(mode)` + `Instrument.output_mode`
select the writer per instrument; `scheduler.cfg` export renders legacy lines.

## Actions Taken

- **D1** `writers/fits/legacy.py` `LegacyFitsWriter` (subclass + warning
  COMMENTs); `get_writer(mode)`; `Instrument.output_mode`.
- **D2** `recorder.start` takes an optional `writer`; record route + scheduler
  pass `get_writer(inst.output_mode)`.
- **D3** `services/legacy_export.build_scheduler_cfg` +
  `GET /api/v1/schedules/export/scheduler.cfg`.
- **D4** tests -- writer-mode selection + legacy comments + export format.

## Verification

Gate green: vulture/black/ruff/flake8/mypy (97 files)/pytest (**97 passed**).

## Milestone M8 + v0.2 -- complete

S024-S025 logged. An existing station imports its config and records in legacy
mode for the archive. Version -> v0.2.2; tag v0.2.2; **0.2-dev merged to main**.
v0.2 "Real, safe, drop-in" is released: the station is unattended (M6),
field-safe (M7, gate held), and a drop-in for existing stations (M8).

## Lessons

- Subclassing the standard writer for legacy mode (just adding the warning cards)
  kept the two writers from diverging -- the image/axes/core header are shared and
  archive-shaped already.

## Tag

``v0.2.2`` at the M8-complete commit; merged to ``main``.
