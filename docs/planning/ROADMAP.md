# Roadmap — e-Callisto NG

Single source of truth for milestone state. Detail lives in milestone plans;
this scans in under a minute. Milestones are seeded from
`e-Callisto-NG-DESIGN.md` section 18.

## In progress

### M0 — Core contracts + record loop  (IN PROGRESS)

Define the seams first; the record loop proves them. Getting M0 right is what
makes M1–M5 cheap.

| Item | State |
| -- | -- |
| Repo scaffold + quality gate (black/ruff/flake8/mypy/pytest/vulture) | done |
| `core` domain models (spectra, capabilities, units) | done |
| Plugin contracts (`InstrumentDriver`, `OutputWriter`, `UploadTransport`) | done |
| `FakeDriver` (hardware-free) + contract tests | done |
| Callisto serial driver (class-1 heterodyne) against the contract | next |
| FITS `OutputWriter` (standard mode) | next |
| Acquisition service: drive → buffer → write loop | next |
| CLI entry point to run a recording with the fake or Callisto driver | next |

Completion criteria: a recording runs end-to-end (fake driver → FITS on disk)
via CLI, quality gate green, contracts documented as ADRs.

## Planned (post-M0)

- **M1** — Backend + portal + auth + wizard (FastAPI, SQLite, Jinja portal on the
  shared M3 design system, login/RBAC, install wizard, instrument setup).
- **M2** — Live & data (WebSocket waterfall island, live viewer, data browser).
- **M3** — Programs & scheduling (freq-program editor + overview generation,
  sun-relative scheduler).
- **M4** — Distribution & health (uploader, dispatch modes, health/alerts).
- **M5** — Calibration & diagnostics; packaging (.deb + SD image).
- **M6+** — SDR classes (class-2 host-DSP, class-3 FPGA drivers) on the M0 seams.

## Conventions

Work traces to a milestone. Full sprint/logbook ceremony is adopted once a
delivery cadence exists (see `CLAUDE.md`). Backlogs: `BUG_BACKLOG.md`,
`FEATURE_BACKLOG.md`. Decisions: `../architecture/decisions/ADR_INDEX.md`.
