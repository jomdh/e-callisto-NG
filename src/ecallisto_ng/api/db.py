# SPDX-License-Identifier: AGPL-3.0-or-later
"""SQLite persistence via SQLModel.

One file-backed database per station (WAL mode for concurrent reads while the
acquisition/upload services write). The engine is created from settings; models
register against ``SQLModel.metadata`` and are created by ``init_db``.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator

from sqlalchemy import event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlmodel import Session, SQLModel, create_engine

from ecallisto_ng.api.settings import get_settings

logger = logging.getLogger(__name__)

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


def _add_missing_columns(engine: Engine) -> None:
    """Add columns the models gained to existing tables (SQLite migration).

    ``create_all`` only creates *missing tables*, never new columns -- so a
    station upgraded over an existing DB would hit "no such column". For each
    registered table that already exists, add any column the model has but the
    table lacks, with the model's default. New (nullable / defaulted) columns
    only -- this never drops or retypes anything.
    """
    insp = inspect(engine)
    for name, table in SQLModel.metadata.tables.items():
        if not insp.has_table(name):
            continue
        present = {c["name"] for c in insp.get_columns(name)}
        for col in table.columns:
            if col.name in present:
                continue
            coltype = col.type.compile(engine.dialect)
            ddl = f'ALTER TABLE "{name}" ADD COLUMN "{col.name}" {coltype}'
            default = getattr(col.default, "arg", None)
            if not col.nullable:
                up = coltype.upper()
                if default is None or callable(default):
                    # A callable/None default needs a type-correct constant.
                    # A datetime column must NOT get DEFAULT 0 (it reads back
                    # as int 0 and breaks fromisoformat on every row); SQLite
                    # also forbids a non-constant default (CURRENT_TIMESTAMP)
                    # in ALTER -- so add it nullable (existing rows NULL).
                    if "CHAR" in up or "TEXT" in up:
                        ddl += " DEFAULT ''"
                    elif "DATE" in up or "TIME" in up:
                        pass  # nullable, no default
                    else:
                        ddl += " DEFAULT 0"
                else:
                    value = (
                        repr(default) if isinstance(default, str) else default
                    )
                    ddl += f" DEFAULT {value}"
            try:
                with engine.begin() as conn:
                    conn.execute(text(ddl))
            except OperationalError as exc:
                # Two processes (web + acquire) can migrate at once on a shared
                # boot; a lost race is harmless if the column now exists.
                if "duplicate column" in str(exc).lower():
                    continue
                raise
            logger.info("migrated: added %s.%s", name, col.name)


def init_db() -> None:
    """Create all registered tables, then add any new columns."""
    # Ensure every model is registered on SQLModel.metadata before create_all
    # / the column migration -- otherwise a caller that ran init_db before
    # importing the models would silently skip those tables (no create, no
    # ALTER), surfacing later as "no such column".
    import ecallisto_ng.api.models  # noqa: F401

    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    _add_missing_columns(engine)


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a session."""
    with Session(get_engine()) as session:
        yield session


def reset_engine_for_tests() -> None:
    """Drop the cached engine so a test can point at a fresh database."""
    global _engine
    _engine = None
