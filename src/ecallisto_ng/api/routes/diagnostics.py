# SPDX-License-Identifier: AGPL-3.0-or-later
"""Station diagnostics: a self-check + a downloadable report for dev."""

from __future__ import annotations

import subprocess
from typing import cast

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlmodel import Session as DbSession

from ecallisto_ng.api.auth import require_role
from ecallisto_ng.api.db import get_session
from ecallisto_ng.api.models import Role
from ecallisto_ng.services.diagnostics import run_self_check

router = APIRouter(prefix="/api/v1/diagnostics", tags=["diagnostics"])

_viewer = require_role(Role.VIEWER)
_operator = require_role(Role.OPERATOR)


@router.get("", dependencies=[Depends(_viewer)])
def diagnostics(db: DbSession = Depends(get_session)) -> dict[str, object]:
    """Run the station self-check now."""
    return run_self_check(db)


def _log_tail() -> str:
    out: list[str] = []
    for unit in ("ecallisto-web", "ecallisto-acquire"):
        try:
            res = subprocess.run(
                ["journalctl", "-u", unit, "-n", "40", "--no-pager"],
                capture_output=True,
                text=True,
                timeout=8,
            )
            out.append(f"== {unit} ==\n{res.stdout.strip()}")
        except (OSError, subprocess.SubprocessError):
            out.append(f"== {unit} == (logs unavailable)")
    return "\n\n".join(out)


@router.get(
    "/report",
    dependencies=[Depends(_operator)],
    response_class=PlainTextResponse,
)
def report(db: DbSession = Depends(get_session)) -> PlainTextResponse:
    """A plain-text diagnostics bundle (checks + logs) to send to dev."""
    rep = run_self_check(db)
    lines = [
        f"e-Callisto NG diagnostics report  -  {rep['generated_utc']}",
        f"overall: {str(rep['status']).upper()}",
        "",
    ]
    for c in cast(list[dict[str, str]], rep["checks"]):
        lines.append(f"[{c['status'].upper():>4}] {c['name']}: {c['detail']}")
    lines += ["", "--- recent service logs ---", "", _log_tail()]
    return PlainTextResponse(
        "\n".join(lines),
        headers={
            "Content-Disposition": (
                "attachment; filename=ecallisto-diagnostics.txt"
            )
        },
    )
