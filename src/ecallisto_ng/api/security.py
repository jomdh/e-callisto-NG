"""Password hashing and session-token minting.

Argon2id for passwords (memory-hard); URL-safe random tokens for sessions.
"""

from __future__ import annotations

import secrets

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_hasher = PasswordHasher()

SESSION_COOKIE = "ecallisto_session"
SESSION_TTL_SECONDS = 12 * 3600


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def new_session_token() -> str:
    return secrets.token_urlsafe(32)
