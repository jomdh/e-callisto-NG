"""SQLite persistence via SQLModel.

One file-backed database per station (WAL mode for concurrent reads while the
acquisition/upload services write). The engine is created from settings; models
register against ``SQLModel.metadata`` and are created by ``init_db``.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from ecallisto_ng.api.settings import get_settings

_engine: Engine | None = None


def _enable_wal(engine: Engine) -> None:
    @event.listens_for(engine, "connect")
    def _set_pragma(dbapi_conn, _rec):  # type: ignore[no-untyped-def]
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()


def get_engine() -> Engine:
    """Return the process-wide engine, creating it on first use."""
    global _engine
    if _engine is None:
        url = get_settings().db_url
        connect_args = (
            {"check_same_thread": False} if url.startswith("sqlite") else {}
        )
        _engine = create_engine(url, connect_args=connect_args)
        if url.startswith("sqlite"):
            _enable_wal(_engine)
    return _engine


def init_db() -> None:
    """Create all registered tables."""
    SQLModel.metadata.create_all(get_engine())


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a session."""
    with Session(get_engine()) as session:
        yield session


def reset_engine_for_tests() -> None:
    """Drop the cached engine so a test can point at a fresh database."""
    global _engine
    _engine = None
