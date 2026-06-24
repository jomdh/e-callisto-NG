# Sprint 0.1-M2-S011 -- data browser + quicklooks + download (M2 close)

**Sprint Goal:** Browse recorded FITS files in the portal, see a quicklook
image, and download them. Closes M2.

**Full ID:** 0.1-M2-S011  **Milestone:** M2 (final)  **Branch:** ``0.1-dev``  **Status:** Planned.

## Decision

A scan-based catalog (no DB table): the data dir is the source of truth; the
catalog reads FITS headers on demand. Quicklook PNGs are generated lazily (Pillow)
and cached in a quicklook dir. Keeps `services` free of an `api` dependency and
avoids index drift. Download is path-traversal-safe (basename only, parent must
be the data dir).

## Deliverables (5)

| # | Task | Layer | Notes |
| -- | -- | -- | -- |
| D1 | `services/catalog.py` | services | `list_recordings(dir)`, `quicklook_png(fits, out)` (Pillow) |
| D2 | `routes/data.py` API | api | GET /files, /files/{name}/download, /files/{name}/quicklook |
| D3 | `GET /portal/data` page | api | listing with quicklook thumbnails + download links |
| D4 | `templates/portal/data.html` + dashboard link | api | M3-styled browser |
| D5 | tests + milestone close | tests/docs | record -> listed -> download -> quicklook; v0.1.2, tag, push |

## Acceptance Criteria

- [ ] After a recording, GET /files lists it with instrument + shape + size.
- [ ] Download returns the FITS bytes; traversal attempts are rejected (404).
- [ ] Quicklook returns a PNG generated from the image.
- [ ] Gate green; M2 tagged v0.1.2.

## Out of Scope

In-browser FITS viewer, light-curve/overview browsers, retention (M4).
