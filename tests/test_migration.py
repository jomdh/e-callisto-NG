# SPDX-License-Identifier: AGPL-3.0-or-later
"""SQLite mini-migration: new model columns are added to an existing table."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, inspect, text

from ecallisto_ng.api import db as dbmod
from ecallisto_ng.api import models  # noqa: F401 -- register tables


def test_add_missing_columns(tmp_path: Path) -> None:
    eng = create_engine(f"sqlite:///{tmp_path}/old.db")
    # an "old" instrument table missing the new program_id column + a row
    with eng.begin() as c:
        c.execute(
            text("CREATE TABLE instrument (id INTEGER PRIMARY KEY, name TEXT)")
        )
        c.execute(text("INSERT INTO instrument (id, name) VALUES (1, 'OLD')"))

    dbmod._add_missing_columns(eng)

    cols = {col["name"] for col in inspect(eng).get_columns("instrument")}
    assert "program_id" in cols  # the new column was added
    assert "address" in cols  # other new columns too
    # the existing row survives; program_id is NULL (nullable)
    with eng.begin() as c:
        row = c.execute(
            text("SELECT name, program_id FROM instrument WHERE id=1")
        ).first()
    assert row is not None
    assert row[0] == "OLD" and row[1] is None
