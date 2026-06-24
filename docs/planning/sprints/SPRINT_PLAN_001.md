# Sprint 0.1-M0-S001 -- project scaffold, core contracts, fake driver

**Sprint Goal:** Establish a lint-clean, hardware-free foundation whose
plugin contracts let M1+ be built against stable seams.

**Full ID:** 0.1-M0-S001
**Version:** 0.1  **Milestone:** M0  **Theme:** M0 housekeeping + the seam
**Duration:** single-session (2026-06-24)
**Branch:** ``main`` (initial repo commit)
**Status note:** documented retroactively when sprint discipline was adopted
(S003 onward is planned before execution).

## Trigger

Greenfield kickstart of the coding phase after the design (`DESIGN`) and
working agreement (`CLAUDE.md`) were settled. M0's mandate (DESIGN section 18):
*define the contracts first; the record loop proves them.*

## Decision

Build `core` as a dependency-free package of domain models + `Protocol`
contracts, and prove the seam with a synthetic `FakeDriver` before touching
hardware. Rationale: getting the seams right up front is what makes the later
milestones cheap (DESIGN 5a). Plain dataclasses (no pydantic/numpy) keep `core`
importable by any layer.

## Deliverables

| # | Task | Layer | Notes |
| -- | -- | -- | -- |
| D1 | Repo scaffold + quality-gate tooling | infra | src-layout, pyproject (black 79/ruff/flake8/mypy/pytest/vulture), .gitignore, .env.example, README, vulture whitelist |
| D2 | `core` domain models | core | units enums, spectra/capabilities value types |
| D3 | Plugin contracts | core | InstrumentDriver, OutputWriter, UploadTransport (Protocols, versioned) |
| D4 | `FakeDriver` + contract tests | drivers | hardware-free synthetic instrument; conformance + behavior tests |
| D5 | Planning tree + seed ADRs | docs | ROADMAP, backlogs, ADR index + ADR-0001/0002/0003 |

## Acceptance Criteria

- [x] Quality gate green (vulture/black/flake8/ruff/mypy/pytest).
- [x] `FakeDriver` satisfies `InstrumentDriver` (runtime + mypy).
- [x] `core` imports nothing concrete.
- [x] Design, CLAUDE.md, planning tree, seed ADRs in place.

## Out of Scope

Real hardware/serial; FITS writer; web/API; acquisition loop.

## Tag target

None (pre-release scaffolding).
