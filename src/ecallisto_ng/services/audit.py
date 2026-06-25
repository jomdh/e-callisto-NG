# SPDX-License-Identifier: AGPL-3.0-or-later
"""Append-only audit log (ADR-0006).

One entry point: ``record``. Best-effort -- an audit-write failure is logged
but never blocks the audited action. Never write secrets to ``detail``.
"""

from __future__ import annotations

import logging

from sqlmodel import Session

from ecallisto_ng.api.models import AuditEvent

_log = logging.getLogger(__name__)


def record(
    db: Session,
    actor: str,
    action: str,
    detail: str = "",
    target: str = "",
) -> None:
    """Append an audit event (best-effort)."""
    try:
        db.add(
            AuditEvent(
                actor=actor, action=action, detail=detail, target=target
            )
        )
        db.commit()
    except Exception:  # noqa: BLE001 - auditing must not break the action
        _log.exception("audit write failed: %s by %s", action, actor)
