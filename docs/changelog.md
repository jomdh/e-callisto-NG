# Changelog

Operator-perspective notes: what each release lets a station do.

## v0.2.0 -- 2026-06-25 (Milestone M6)

The station now runs itself.

- **Records on schedule, unattended.** Once an instrument has a schedule, the
  station starts and stops recording on the sun-relative (or fixed) window with
  no operator action -- files roll over automatically.
- **Uploads itself.** Targets set to "immediate" send each finished file as it's
  written; "overnight"/scheduled targets send within their window. Old local
  files are pruned once safely uploaded (un-uploaded data is never deleted).
- **Calibrated output.** Assign a calibration set and unit to an instrument to
  record SFU or Kelvin FITS; raw stays the default otherwise.
- **Light curves.** Flagged channels are written as per-channel time-series CSVs.

Internal: scheduler + uploader background loops, retention pruning, calibration
wired through the recorder, light-curve writer; 76 tests; sprints S018-S020.

## v0.1.5 -- 2026-06-25 (Milestone M5, v0.1 release)

Calibrate, diagnose, and install.

- **Optional calibration.** Attach calibration coefficients to produce solar-flux
  (SFU) or antenna-temperature (Kelvin) FITS instead of raw counts. Off by
  default -- raw is always the default unless you explicitly calibrate.
- **Device diagnostics.** Probe an instrument from the portal/API to confirm it
  responds and report its model, firmware, and capabilities.
- **Install on a station.** A systemd service and an install script set the suite
  up on any Debian/Raspberry Pi OS machine (a `.deb` recipe is outlined for later).

This is the **v0.1 release** -- a station can be installed, set up in the browser,
record real Callisto data to FITS, watch it live, schedule it to the Sun, browse
and upload it, and monitor health.

Internal: pure calibration math (SFU/Kelvin) applied in the writer, diagnostics
endpoint, packaging (systemd + install.sh); 69 tests; sprints S016-S017.
Merged 0.1-dev -> main.

## v0.1.4 -- 2026-06-25 (Milestone M4)

Get your data off the station and keep an eye on it.

- **Upload to a destination.** Configure where recorded files go (a local
  mirror/mounted drive, or an FTP server), then send them -- gzipped, once each,
  never re-sent. Failed files are recorded so you can see what didn't go.
- **System health.** A health page (and API) shows disk space, instrument and
  recording counts, and how many files are waiting to upload, with alerts when
  something needs attention (disk low, no instruments, upload backlog).

Internal: pluggable upload transports (local/FTP) behind the contract, uploader
with gzip + tmp-then-rename + job tracking, health service with pure alert logic;
64 tests; sprints S014-S015.

## v0.1.3 -- 2026-06-25 (Milestone M3)

Plan what and when to observe.

- **Frequency programs.** Define which channels to observe by hand, or
  auto-generate a program from a spectral overview -- the suite picks the
  quietest (least-interference) channel in each step.
- **Sun-relative scheduling.** Set a schedule that follows the Sun for your
  station's coordinates (computed with proper astronomy, no external calendar
  tools), with adjustable margins; preview today's recording window.

Internal: astropy sunrise/transit/sunset, frequency-program model + generator,
schedule model + preview; 58 tests; sprints S012-S013.

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
