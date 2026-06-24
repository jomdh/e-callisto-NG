# Changelog

Operator-perspective notes: what each release lets a station do.

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
