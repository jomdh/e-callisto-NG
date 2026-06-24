# Changelog

Operator-perspective notes: what each release lets a station do.

## v0.1.2 -- 2026-06-25 (Milestone M2)

See and retrieve your data in the browser.

- **Live waterfall.** Open an instrument's live page and watch its spectrogram
  scroll in real time as it records, rendered in your browser.
- **Data browser.** Browse recorded FITS files with quicklook thumbnails, sizes,
  and observation times; download any file with one click.

Internal: WebSocket frame hub (recorder -> browser), scan-based file catalog,
lazy Pillow quicklooks, path-traversal-safe downloads; 50 tests; sprints S010-S011.

## v0.1.1 -- 2026-06-25 (Milestone M1)

The station is now operated from a browser.

- **First-run setup wizard.** Opening a fresh station sends you to a setup page:
  create the administrator (no default password exists), name the station and its
  observatory + coordinates, and add a first instrument -- no terminal needed.
- **Log in and see your station.** A themed portal (dark "Nebula" / light
  "Supernova") with a login page and a dashboard listing your instruments, sharing
  the visual language of the wider doncel platform.
- **Manage instruments.** Register, edit, and remove instruments; start and stop a
  recording on one and see the resulting FITS path -- all over the API.
- **Roles.** Admin / operator / viewer accounts with server-side sessions; viewers
  can look, operators can act, admins can manage.

Internal: FastAPI + SQLite (SQLModel), argon2 auth, server-rendered Jinja portal +
M3 design system, 44 tests, sprints S005-S009.

## v0.1.0 -- 2026-06-25 (Milestone M0)

The foundation: a station can record a Callisto spectrogram to a FITS file from
the command line, with no web app yet.

- **Record from the command line.** `ecallisto-ng record` drives an instrument
  and writes a standard FITS file (8-bit time x frequency, raw ADC), printing the
  path. Works against a real Callisto over serial (`--driver callisto --port ...`)
  or a built-in hardware-free simulator (`--driver fake`) for trying it out.
- **Real Callisto support.** The class-1 (heterodyne) Callisto serial protocol is
  implemented -- firmware 1.5/1.7/1.8 detection, channel/EEPROM programming, and
  the swept-ADC data stream -- behind a clean driver interface.
- **Archive-shaped output.** FITS files carry the standard header (observation
  times, observatory coordinates, frequency file, gain) and a time/frequency
  axis table, so they fit existing e-Callisto tooling.
- **Built for what comes next.** Everything sits behind versioned plugin
  contracts (instrument driver, output writer, connection, upload transport), so
  SDR instruments, more output formats, and the web suite layer on without
  rework.

Internal: src-layout Python package, full quality gate (black/ruff/flake8/mypy/
pytest/vulture), 30 tests, ADRs 0001-0004, sprints S001-S004.
