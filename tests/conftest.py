import os
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
# UI tests must never touch the real database: point the app at a throw-away file before it is imported.
os.environ["MATEIS_DB_PATH"] = str(Path(tempfile.mkdtemp()) / "ui_tests.db")

pytest_plugins = ["nicegui.testing.user_plugin"]

from core.selection.database import MaterialDatabase  # noqa: E402

SEED = ROOT / "data" / "materials_seed.json"


@pytest.fixture
def seed_path():
    return SEED


@pytest.fixture
def db(tmp_path):
    database = MaterialDatabase(tmp_path / "test.db")
    database.seed_from_json(SEED)
    return database


@pytest.fixture
def df(db):
    return db.to_dataframe()
