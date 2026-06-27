# e-Callisto NG

Web-based solar radio spectrometer suite that runs **on a station** (a
Debian/Raspbian computer, often a low-power Raspberry Pi) and controls one or
more instruments, fully operated from a browser.

- **Design (source of truth):** [`e-Callisto-NG-DESIGN.md`](e-Callisto-NG-DESIGN.md)
- **Install a station:** [`DEPLOYMENT.md`](DEPLOYMENT.md) ·
  **Operate one (incl. remote recovery):** [`OPERATIONS.md`](OPERATIONS.md)
- **Working agreement:** [`CLAUDE.md`](CLAUDE.md)
- **License & governance:** [`LICENSE`](LICENSE), [`GOVERNANCE.md`](GOVERNANCE.md)
- **Planning, ADRs, and changelog** live under a local, gitignored `docs/`
  folder (kept on the maintainer's machine, not part of this repo).
- **Legacy analysis** (Windows/Linux predecessors) lives in a local, gitignored
  `legacy/` folder — reverse-engineering reference, not part of this repo.

## Run on a Raspberry Pi station

Pull the repo onto the station and run it — reachable over the LAN/VPN:

```bash
git clone https://github.com/jomdh/e-callisto-NG.git
cd e-callisto-NG
./scripts/run.sh
```

The first run creates a virtualenv (with `--system-site-packages` so a
system/conda **SoapySDR** stays visible for the RX-888), writes a `.env` with a
generated secret key, and starts the server on `0.0.0.0:8000`. Open the printed
URL and complete the setup wizard (no default credentials). To update later:
`git pull && ./scripts/run.sh`.

- **Find hardware:** `python3 scripts/scan_devices.py` lists serial ports +
  USB SDRs; `--probe` confirms a Callisto handshake. The RX-888 line reports
  REAL (SoapySDR `driver=rx888`) vs SYNTHETIC.
- **Production install** (system user + systemd + `/opt`): `sudo
  ./scripts/install.sh`.
- **SoapySDR in conda:** if SoapySDR lives only in a conda env, activate it and
  run `pip install -e .` there instead of using the venv.

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
