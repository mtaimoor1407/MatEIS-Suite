"""Lazily created, shared database services for the UI."""
from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path

import config
from core.corrosion.emf import EMFDatabase
from core.exceptions import DatabaseError
from core.selection.database import MaterialDatabase
from core.storage import HistoryStore


@dataclass
class Services:
    materials: MaterialDatabase
    emf: EMFDatabase
    history: HistoryStore
    db_path: Path


_services: Services | None = None


def _open(path: Path) -> Services:
    svc = Services(MaterialDatabase(path), EMFDatabase(path), HistoryStore(path), path)
    if svc.materials.count() == 0:
        svc.materials.seed_from_json(config.MATERIALS_SEED)
    if svc.emf.count() == 0:
        svc.emf.seed_from_json(config.EMF_SEED)
    return svc


def get_services() -> Services:
    """Open the SQLite file (seeding it on first run); fall back to a temp file if the folder is read-only."""
    global _services
    if _services is None:
        try:
            _services = _open(config.DB_PATH)
        except (DatabaseError, OSError):
            _services = _open(Path(tempfile.gettempdir()) / "mateis.db")
    return _services


def reset_services() -> None:
    """Forget the cached services (used by tests that change MATEIS_DB_PATH)."""
    global _services
    _services = None
