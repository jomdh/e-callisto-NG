# Changelog

Operator-perspective notes: what each release lets a station do.

## v0.5.3 -- 2026-06-25 (Milestone M18, v0.5 release)

A guided first run that you can't lose your place in.

- **Multi-step setup wizard.** Set up a fresh station step by step -- admin,
  station, coordinates, first instrument, review -- and a refresh or reboot
  resumes exactly where you left off.
- **Migrate in the wizard.** Paste a legacy `callisto.cfg` and the wizard
  pre-fills the station and instrument for you.

This is the **v0.5 release** -- station completeness: user management + audit
(M15), degrade-don't-die resilience + alerts + independent acquisition (M16),
support bundle + updates + SD image (M17), and the full setup wizard (M18).

Internal: WizardState + multi-step resumable wizard, legacy-import branch; 176
tests; sprint S043. Merged 0.5-dev -> main.

## v0.5.2 -- 2026-06-25 (Milestone M17)

Ship it, keep it current, get help fast.

- **Support bundle.** One click downloads a bundle of versions, system info,
  configuration, and audit log -- with all secrets redacted -- to send for
  support (replaces the old remote-desktop step).
- **Update status.** See the running version and the channel the station tracks.
- **SD-card image.** A build recipe produces a flashable Raspberry Pi OS image
  with the suite preinstalled and both services enabled.

Internal: support_bundle (redacted zip), updates version reporting,
build-sd-image.sh (pi-gen); 174 tests; sprint S042. (Config backup/restore: M15.)

## v0.5.1 -- 2026-06-25 (Milestone M16)

Hard to knock over.

- **Degrade, don't die.** A clear policy decides what happens on each fault: disk
  full pauses recording, a vanished receiver auto-reconnects, an upload backlog
  keeps recording (never lose data), and a web-app problem never stops
  acquisition.
- **Always alert.** Send health alerts to email or a webhook; test a channel
  before relying on it.
- **Independent acquisition.** Recording can run as its own supervised service,
  so restarting the web app never interrupts it.
- **Clock drift gate.** Optionally pause recording when the clock drifts beyond a
  tolerance.

Internal: failure_modes matrix, alerts (AlertChannel + webhook/email), ADR-0007
acquisition daemon (`ecallisto-ng acquire` + unit) + run_loops_in_web, drift gate;
170 tests; sprints S040-S041.

## v0.5.0 -- 2026-06-25 (Milestone M15)

Run the station, not just the science.

- **User management + audit log.** Admins create accounts, set roles, and disable
  users; every security-sensitive action (and each login) is recorded in an
  append-only audit log.
- **Config backup & restore.** Download the whole station configuration
  (instruments, schedules, programs, calibration, targets, access) and restore it
  -- the fast path to provisioning a second station.
- **System & settings page.** See version, disk usage, clock sync, and retention
  at a glance.

Internal: AuditEvent + services/audit (ADR-0006), user CRUD, config_backup
export/import, system-info endpoint, Settings/Audit pages; 161 tests; sprints
S038-S039.

## v0.4.3 -- 2026-06-25 (Milestone M14, v0.4 release)

Get your data out, and plan around interference.

- **SFTP uploads.** Ship files over SFTP (in addition to FTP and local mirrors),
  with the same safe upload-then-rename behaviour.
- **Dated backup archive.** Optionally move uploaded files into a dated
  `YYYY/MM/DD` archive (the legacy FITbackup) instead of deleting them.
- **Smarter frequency programs.** Generate programs that avoid an RFI band you
  exclude, and convert between RF and IF for up/down-converters.
- **Test a destination.** Check that an upload target is reachable before relying
  on it.

This is the **v0.4 release** -- legacy Windows parity: recorder behaviours (M11),
bench tools (M12), spectrum viewer + light-curve publication (M13), and
distribution + generator (M14). Existing heterodyne stations can migrate without
losing functionality.

Internal: transports/sftp.py (paramiko), uploader archive + connection test,
freqgen exclude_band + rf_to_if; 151 tests; sprints S036-S037. Merged 0.4-dev -> main.

## v0.4.2 -- 2026-06-25 (Milestone M13)

See your spectra and publish your light curves.

- **Spectrum viewer.** Open any overview/spectrum file and explore it: LO
  conversion, dB/log scaling, background subtraction, typed-range zoom, and PNG
  export -- the legacy SXY/M9703A plotter, web-native.
- **dB toggle.** Switch the live view and the viewer between raw and dB (never
  automatic -- raw stays the default).
- **Public light-curve images.** Render a day's light curve as a 24-hour UT PNG
  with up to 10 coloured channels -- the website image the legacy wwwgeni made.
- **Richer live view.** The live page now shows the waterfall plus a single
  spectrum y(f) and a light curve y(t) of the peak channel.

Internal: services/spectrum.py + viewer island, services/lightcurve_png.py
(Pillow), spectra/lightcurve endpoints, live panels; 143 tests; sprints S034-S035.

## v0.4.1 -- 2026-06-25 (Milestone M12)

The commissioning bench, web-native.

- **Detector readout.** Tune a frequency, set the gain, and read the detector
  voltage live -- the legacy "simple" signal-check tool, on a Tools page.
- **Noise figure.** Run a cold/warm/hot Y-factor noise-figure measurement and see
  the noise figure, detector slope, and overall bandpass -- the legacy
  NoiseFigurePlotter workflow.

Bench tools are available on heterodyne instruments (not while recording).
Internal: BenchCapable contract (ADR-0005), services/bench.py + noise_figure.py,
bench endpoints, Tools page; 135 tests; sprints S032-S033.

## v0.4.0 -- 2026-06-25 (Milestone M11)

Legacy recorder parity, part 1 -- what fielded heterodyne stations rely on daily.

- **Data-loss watchdog.** A garbled receiver stream auto-stops with the familiar
  "Check RS232-connection!" warning, the good data so far is kept, and recording
  auto-restarts -- no lost science, no stuck recorder.
- **Scheduled overviews.** A schedule can trigger a 45-870 MHz spectral overview
  at a set time (and you can run one on demand), written as the legacy
  OVS .prn/.csv pair.
- **Program-driven schedules.** A schedule records with a chosen frequency
  program, including its light-curve channel flags.
- **Legacy light-curve files.** Flagged channels are written as the legacy daily
  `LC<date>_<ADU|SFU>_<instrument>.txt` (up to 10 channels).

Internal: services/watchdog.py + acquisition wiring; services/overview.py;
Schedule.program_id/overview_at, FrequencyProgram light-curve indices; console UI
fields/actions; 123 tests; sprints S030-S031.

## v0.3.2 -- 2026-06-25 (Usability)

Everything is now clickable.

- **Full portal navigation.** A top nav reaches every section: Instruments,
  Schedules, Frequency programs, Calibration, Uploads, Data, Fleet, Access,
  Import, System.
- **Manage from the browser.** Create/list/delete instruments, schedules,
  programs, calibration sets, upload targets, and fleet peers -- and run
  instrument actions (record, stop, diagnose, live) -- without touching the API.
- **Settings pages.** Remote-access configuration (with a one-click Caddyfile),
  legacy-station import (with dry-run preview), and the fleet overview.

Previously these backends were reachable only through the API docs. Internal:
config-driven CRUD island + settings island (CSP-safe JS over the cookie-authed
API), nav partial, management/settings routes; 114 tests; sprint S029.

## v0.3.1 -- 2026-06-25 (Milestone M10, v0.3 release)

Oversee a whole observatory, not just one station.

- **Fleet view.** Register your other stations and see them all in one place --
  each station's disk, instruments, recordings, upload backlog, and alerts --
  with unreachable stations clearly flagged.
- Stations share health over a token-gated endpoint, so an observatory can poll
  them without sharing logins.

This is the **v0.3 release** -- SDR instruments (host-DSP and FPGA) join the
classic receiver, and an observatory can watch its fleet of stations.

Internal: shared station-health builder, PeerStation registry, token-gated
fleet-health endpoint, pure injectable fleet aggregation; 109 tests; sprint S028.
Merged 0.2-dev -> main.

## v0.3.0 -- 2026-06-25 (Milestone M9)

Beyond the classic receiver: software-defined radios.

- **SDR support.** Two new instrument types record through the exact same suite
  as the classic Callisto: an **SDR with host-side processing** (the station's CPU
  turns raw radio into a spectrogram) and an **SDR with an on-board FPGA** (the
  device does the processing and streams ready spectra over the network).
- Pick the instrument type when you add it; everything else -- recording,
  scheduling, live view, uploads, calibration -- works unchanged.

Internal: SoftSdrDriver (FFT host DSP), FpgaSdrDriver + NetworkConnection +
simulator, registered in the driver factory; all three instrument classes share
one pipeline; 105 tests; sprints S026-S027.

## v0.2.2 -- 2026-06-25 (Milestone M8, v0.2 release)

A drop-in upgrade for existing stations.

- **Import a legacy station.** Paste an existing station's `callisto.cfg`,
  frequency, scheduler, and calibration files and the suite recreates the
  instrument, coordinates, program, schedule, and calibration -- no re-setup.
- **Archive-compatible output.** Pick "legacy" output mode per instrument to write
  FITS the existing e-Callisto archive expects, and export a `scheduler.cfg`.

This is the **v0.2 release** -- the station now runs unattended (M6), is safe to
expose and simple to ship (M7), and is a drop-in for existing stations (M8).

Internal: legacy config parsers + import endpoint, LegacyFitsWriter + writer
registry + per-instrument output mode, scheduler.cfg export; 97 tests; sprints
S024-S025. Merged 0.2-dev -> main.

## v0.2.1 -- 2026-06-25 (Milestone M7)

Safe to expose and simple to ship.

- **Encrypted credentials.** Upload passwords are stored encrypted and never
  shown again -- the API only reports whether one is set.
- **Hardened browser security.** A Content-Security-Policy is enforced on every
  page.
- **Remote access your way.** Choose LAN/VPN, public HTTPS with dynamic DNS, or
  an outbound relay tunnel; the matching Caddy config is generated for you.
- **Clock awareness.** Health shows real NTP synchronization; recording can be
  set to pause if the clock is known out of sync.
- **One-command install.** A Debian package sets up the user, service, and a
  generated secret on install.

Internal: Fernet credential encryption, CSP middleware + nonce, access settings +
Caddyfile/DDNS generation, timedatectl clock probe + gate, debian/ packaging;
87 tests; sprints S021-S023.

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
