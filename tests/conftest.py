"""Shared fixtures: an app + client bound to a throwaway SQLite database."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ecallisto_ng.api import db
from ecallisto_ng.api.settings import get_settings


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    os.environ["ECALLISTO_DB_URL"] = f"sqlite:///{tmp_path / 'test.db'}"
    os.environ["ECALLISTO_DATA_DIR"] = str(tmp_path / "data")
    get_settings.cache_clear()
    db.reset_engine_for_tests()

    from ecallisto_ng.services.recorder import get_recorder

    get_recorder()._jobs.clear()  # isolate the process-wide recorder

    from ecallisto_ng.api.app import create_app

    with TestClient(create_app()) as c:
        yield c


@pytest.fixture
def db_session(client: TestClient) -> Iterator[object]:
    # client fixture has initialized the engine/tables via lifespan.
    from sqlmodel import Session

    with Session(db.get_engine()) as session:
        yield session
