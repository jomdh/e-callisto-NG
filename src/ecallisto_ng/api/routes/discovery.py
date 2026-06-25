# SPDX-License-Identifier: AGPL-3.0-or-later
"""Hardware discovery endpoint: scan for Callisto / SDR devices."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ecallisto_ng.api.auth import require_role
from ecallisto_ng.api.models import Role
from ecallisto_ng.services import discovery

router = APIRouter(prefix="/api/v1/discovery", tags=["discovery"])

_operator = require_role(Role.OPERATOR)


@router.get("/scan", dependencies=[Depends(_operator)])
def scan(probe: bool = False) -> dict[str, object]:
    """Scan USB-serial + USB for instruments.

    ``probe=true`` also opens each serial port and attempts the Callisto
    handshake (operator action -- it touches the hardware).
    """
    devices = discovery.discover(probe=probe)
    return {
        "probed": probe,
        "count": len(devices),
        "devices": [d.as_dict() for d in devices],
    }
