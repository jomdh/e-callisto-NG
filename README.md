# e-Callisto NG

Web-based solar radio spectrometer suite that runs **on a station** (a
Debian/Raspbian computer, often a low-power Raspberry Pi) and controls one or
more instruments, fully operated from a browser.

- **Design (source of truth):** [`e-Callisto-NG-DESIGN.md`](e-Callisto-NG-DESIGN.md)
- **Working agreement:** [`CLAUDE.md`](CLAUDE.md)
- **Decisions:** [`docs/architecture/decisions/`](docs/architecture/decisions)
- **Roadmap:** [`docs/planning/ROADMAP.md`](docs/planning/ROADMAP.md)
- **Legacy analysis** (Windows/Linux predecessors) lives in a local, gitignored
  `legacy/` folder — reverse-engineering reference, not part of this repo.

## Status

Greenfield, **M0** (core contracts + record loop). The package is a monorepo
with imports flowing inward toward `core`:

```
src/ecallisto_ng/
  core/        domain models + plugin contracts (depends on nothing)
  drivers/     instrument drivers (fake driver lands first; Callisto next)
```

## Develop

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"

# Quality gate (run before every commit)
vulture src/
black --line-length 79 --check src/ tests/
flake8 src/ tests/
ruff check src/ tests/
mypy
pytest
```

No hardware is needed: the `fake` driver emits synthetic spectra so the whole
stack runs in development and CI.

## License

e-Callisto NG is licensed **AGPL-3.0-or-later** — see [`LICENSE`](LICENSE) and
[`GOVERNANCE.md`](GOVERNANCE.md). Plugins (drivers/transports/writers) interact
across versioned contracts + a process boundary and may be independently
licensed, including closed-source. Contributions require a DCO sign-off
([`CONTRIBUTING.md`](CONTRIBUTING.md)).
