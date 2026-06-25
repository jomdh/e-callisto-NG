"""Symmetric encryption for secrets at rest (B2).

Fernet key derived from the station's ``secret_key`` (set per install), so
upload-target credentials are encrypted in the DB and never stored in plaintext
(DESIGN 10). Empty strings round-trip to empty.
"""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet

from ecallisto_ng.api.settings import get_settings


def _fernet() -> Fernet:
    digest = hashlib.sha256(get_settings().secret_key.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt(plaintext: str) -> str:
    if plaintext == "":
        return ""
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt(token: str) -> str:
    if token == "":
        return ""
    return _fernet().decrypt(token.encode()).decode()
