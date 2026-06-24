# Sprint 0.1-M0-S001 -- project scaffold, core contracts, fake driver

**Status:** Completed (2026-06-24)
**Date:** 2026-06-24
**Branch:** ``main``  **Commit:** ``c046142``

## Goal

Establish a lint-clean, hardware-free foundation whose plugin contracts let
M1+ be built against stable seams.

## Goal Met?

**Yes.** `core` holds dependency-free domain models and versioned `Protocol`
contracts; `FakeDriver` proves the seam; the quality gate is green.

## Actions Taken

- **D1 Scaffold.** `pyproject.toml` (setuptools, src-layout, `pythonpath=src`
  so tests run without install), tool configs (black 79, ruff E/F/I/UP/B,
  mypy `disallow_untyped_defs`, vulture, pytest), `.flake8`, `.gitignore`,
  `.env.example`, `README.md`, `vulture_whitelist.py`.
- **D2 Domain models.** `core/units.py` (UnitLevel/ProcessingLocation/LinkKind/
  InstrumentClass), `core/spectra.py` (Channel, Capabilities, InstrumentInfo,
  SpectrumFrame, Housekeeping) as frozen dataclasses.
- **D3 Contracts.** `core/contracts.py` -- `InstrumentDriver`, `OutputWriter`,
  `UploadTransport` as `runtime_checkable` Protocols; `CONTRACT_VERSION` 0.1.0.
- **D4 Fake driver.** `drivers/fake/driver.py` emits a drifting-peak
  spectrogram with injectable clock; `tests/test_contracts.py` (5 tests).
- **D5 Docs.** ROADMAP (from DESIGN 18), BUG/FEATURE backlogs, ADR index +
  ADR-0001 (frontend), ADR-0002 (units), ADR-0003 (license, open).

## Verification

Quality gate green: vulture (with whitelist for Protocol interface params),
black-79, flake8, ruff, mypy, pytest (5 passed). Committed `c046142`, pushed to
`origin/main` (https://github.com/jomdh/e-callisto-NG). `legacy/` gitignored.

## Lessons / Observations

- Vulture flags `Protocol` method parameters (stub bodies) as unused -> a
  documented whitelist is the idiomatic fix; keeps `contracts.py` scanned for
  real rot.
- Keeping `core` dataclass-only (no pydantic/numpy) paid off immediately: the
  fake driver and tests import it with zero transitive deps.

## Tag

None (scaffolding).
