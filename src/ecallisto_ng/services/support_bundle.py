"""Support-bundle export (DESIGN 15 / F5 -- replaces TeamViewer support).

Gathers version, system info, the station config, and recent audit into one zip
an operator can send for support. **Secrets are redacted** -- upload
passwords and the DDNS/relay never appear, and the signing secret is never
included. Asserted in tests.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

from sqlmodel import Session, select

from ecallisto_ng.api.models import AuditEvent
from ecallisto_ng.services import config_backup

_REDACTED = "<redacted>"


def _redact(cfg: dict[str, Any]) -> dict[str, Any]:
    for target in cfg.get("upload_targets", []):
        if target.get("password"):
            target["password"] = _REDACTED
    for access in cfg.get("access", []):
        for key in ("ddns_update_url", "tunnel_relay"):
            if access.get(key):
                access[key] = _REDACTED
    return cfg


def build_support_bundle(
    db: Session,
    out_path: Path,
    version: str,
    system_info: dict[str, Any],
) -> Path:
    """Write a redacted support bundle zip; return its path."""
    cfg = _redact(config_backup.export_config(db))
    audit = [
        e.model_dump(mode="json")
        for e in db.exec(select(AuditEvent).limit(500)).all()
    ]
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("version.txt", version)
        z.writestr("system.json", json.dumps(system_info, indent=2))
        z.writestr("config.json", json.dumps(cfg, indent=2))
        z.writestr("audit.json", json.dumps(audit, indent=2))
    return out_path
