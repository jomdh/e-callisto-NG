# SPDX-License-Identifier: AGPL-3.0-or-later
"""Hardware discovery endpoint: scan for Callisto / SDR devices."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session as DbSession

from ecallisto_ng.api import auth
from ecallisto_ng.api.db import get_session
from ecallisto_ng.api.models import Role, User, role_satisfies
from ecallisto_ng.api.setup import is_configured
from ecallisto_ng.services import discovery

router = APIRouter(prefix="/api/v1/discovery", tags=["discovery"])


@router.get("/scan")
def scan(
    probe: bool = False,
    db: DbSession = Depends(get_session),
    user: User | None = Depends(auth.optional_user),
) -> dict[str, object]:
    """Scan USB-serial + USB for instruments.

    During first-run setup (no admin yet) the wizard may scan unauthenticated;
    once the station is configured, an operator login is required. ``probe``
    also opens each serial port for the Callisto handshake (touches hardware).
    """
    if is_configured(db) and (
        user is None or not role_satisfies(user.role, Role.OPERATOR)
    ):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "operator role required"
        )
    devices = discovery.discover(probe=probe)
    return {
        "probed": probe,
        "count": len(devices),
        "devices": [d.as_dict() for d in devices],
    }
