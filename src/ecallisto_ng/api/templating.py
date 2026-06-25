# SPDX-License-Identifier: AGPL-3.0-or-later
"""Jinja templates and static-file locations for the portal."""

from __future__ import annotations

from pathlib import Path

from fastapi.templating import Jinja2Templates

_HERE = Path(__file__).parent
TEMPLATES_DIR = _HERE / "templates"
STATIC_DIR = _HERE / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
