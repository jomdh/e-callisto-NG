# Sprint 0.1-M5-S017 -- diagnostics + packaging (M5 close, v0.1 release)

**Status:** Completed (2026-06-25)  **Branch:** ``0.1-dev`` -> merged to ``main``

## Goal / Met?

Probe an instrument and install the suite. **Met** -- a diagnose endpoint reports
device info/capabilities; systemd unit + install script set the suite up on a
Debian/Raspbian station. M5 + the v0.1 version close here.

## Actions Taken

- **D1** `GET /instruments/{id}/diagnose` -- builds the driver, connect/identify,
  returns model/firmware/class/bit-depth/capabilities (502 on probe failure).
- **D2** `packaging/systemd/ecallisto-web.service` (uvicorn `create_app
  --factory`, ordered after chrony, Restart=always) + `scripts/install.sh`
  (user, venv, dirs, env, unit, enable).
- **D3** `packaging/README.md` -- installed layout, systemd, quick install, .deb
  plan, time-sync requirement.
- **D4 tests** -- diagnose probes the fake (FAKE/8-bit/heterodyne); systemd unit
  + install script present and valid.
- **D5 version close** -- SNR sweep clean; v0.1.5; changelog; tag `v0.1.5`; merge
  `0.1-dev` -> `main`.

## Verification

Gate green: vulture (SNR clean)/black/ruff/flake8/mypy (75 files)/pytest
(**69 passed**).

## Milestone M5 + v0.1 -- complete

All planned milestones (M0-M5) delivered. A station installs, runs the wizard,
records real Callisto data to FITS, streams it live, schedules to the Sun,
browses/uploads it, monitors health, optionally calibrates, and self-diagnoses.
17 sprints, 5 ADRs, 69 tests, tags v0.1.0-v0.1.5, merged to main.

## Lessons

- The driver contract made diagnostics trivial: the same connect/identify the
  recorder uses *is* the probe, hardware-free via the fake.
- M6+ (SDR class-2/3 drivers) and refinements (credential encryption B2, NTP
  probe, auto-dispatch, bench-tool UI, full .deb) are the next bodies of work,
  all enabled by the seams laid in M0.

## Tag

``v0.1.5`` at the M5-complete commit; merged to ``main``.
