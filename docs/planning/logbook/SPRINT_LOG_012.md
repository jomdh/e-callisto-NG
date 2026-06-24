# Sprint 0.1-M3-S012 -- frequency programs + overview-based generation

**Status:** Completed (2026-06-25)  **Branch:** ``0.1-dev``

## Goal / Met?

Define frequency programs by hand or generated from an overview. **Met** --
`generate_frequencies` selects the quietest channel per bin (or even centers);
programs are CRUD-able and generatable via the API.

## Actions Taken

- **D1 `services/freqgen.py`** -- `generate_frequencies(overview, start, stop,
  n, mode)`: per-bin minimum-amplitude (quiet) or bin-center (even); validated.
- **D2** `FrequencyProgram` model (name, frequencies JSON, band, source).
- **D3 `routes/programs.py`** -- list/create/generate/delete; viewer read /
  operator write.
- **D4 tests** -- quiet picks min, even spacing, validation; CRUD + generate +
  RBAC.

## Verification

Gate green: vulture/black/ruff/flake8/mypy (60 files)/pytest (**55 passed**).

## Lessons

- First cut let the empty-bin fallback short-circuit even mode (returned bin
  lows, not centers); the table-driven test caught it immediately. Restructured
  so mode is decided first, fallback second.

## Tag

None (M3 closes at S013).
