# SPDX-License-Identifier: AGPL-3.0-or-later
"""e-Callisto NG -- web-based solar radio spectrometer suite for a station.

Package layout (imports flow inward toward ``core``):

    core/        domain models + plugin contracts (depends on nothing)
    drivers/     instrument drivers (Callisto first; fake for tests)
    transports/  upload transports (FTP/SFTP/...)
    writers/     output writers (legacy/standard/custom FITS)
    services/    acquisition, scheduler, uploader, jobs
    api/         FastAPI backend + Jinja portal + static islands

See ``e-Callisto-NG-DESIGN.md`` for the full design and ``CLAUDE.md`` for the
working agreement.
"""

from __future__ import annotations

__version__ = "0.9.0"
