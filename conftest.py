"""Pytest session setup: build the SQLite sales store before tests run.

The database (``config.DATA_PATH``) is a gitignored, derived artefact, so a
clean checkout has only the seed CSV. Build it once per session so the tools,
which read from SQLite, have data to read.
"""

import pytest

from config import DATA_PATH
from db.loader import build_database


@pytest.fixture(scope="session", autouse=True)
def _build_sales_database():
    if not DATA_PATH.exists():
        build_database()
    yield
