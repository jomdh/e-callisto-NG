# Sprint 0.7-M23-S051 -- astro source-track planning panel

**Status:** Completed (2026-06-25)  **Branch:** `0.7-dev`

## Goal / Met?
Observation planning (F8). **Met** -- a panel plots a source's elevation across
the day for the station's coordinates against the horizon.

## Actions
- `services/astro_track.py` `source_track` (astropy AltAz; Sun via get_sun,
  planets/Moon via get_body, six strong fixed radio sources via SkyCoord).
- `Station.horizon_deg`; `routes/planning.py` `GET /api/v1/planning/track`
  (source + day -> track + horizon + station).
- `/portal/planning` + planning.js (canvas elevation track, el=0 + station
  horizon lines, max-elevation readout); Planning nav link.

## Verification
Gate green: vulture/black/ruff/flake8/mypy (149 files)/pytest (**209 passed**).

## Lessons
- astropy makes the ephemeris a few lines + exact (Sun >40 deg at solstice is a
  stable golden assertion), so the planner needed no hand-rolled astronomy.

## Tag
None (M23 closes at S052).
