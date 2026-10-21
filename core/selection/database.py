"""SQLite persistence for the materials table (Theme 2).

The class owns every SQL statement, so nothing outside ``core/database.py``
needs to know SQL. All queries are parameterised (no string formatting of
user input), which also protects against SQL injection.
"""
from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

from core.exceptions import (
    DatabaseError,
    DuplicateMaterialError,
    MaterialNotFoundError,
    ValidationError,
)
from core.selection.material import Material
from core.selection.properties import MATERIAL_CLASSES, STRENGTH_BASES

RECORD_COLUMNS = [
    "id", "name", "material_class", "density", "modulus", "strength",
    "cost", "cost_vol", "strength_basis", "source", "verified", "notes",
]

_SCHEMA = f"""
CREATE TABLE IF NOT EXISTS materials (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT    NOT NULL UNIQUE,
    material_class      TEXT    NOT NULL CHECK (material_class IN ({", ".join(repr(c) for c in MATERIAL_CLASSES)})),
    density_kg_m3       REAL    NOT NULL CHECK (density_kg_m3 > 0),
    youngs_modulus_gpa  REAL    NOT NULL CHECK (youngs_modulus_gpa > 0),
    yield_strength_mpa  REAL    NOT NULL CHECK (yield_strength_mpa > 0),
    cost_usd_per_kg     REAL    NOT NULL CHECK (cost_usd_per_kg > 0),
    strength_basis      TEXT    NOT NULL DEFAULT 'yield' CHECK (strength_basis IN ({", ".join(repr(b) for b in STRENGTH_BASES)})),
    source              TEXT    NOT NULL DEFAULT '',
    notes               TEXT    NOT NULL DEFAULT '',
    verified            INTEGER NOT NULL DEFAULT 0
);
"""

_COLUMNS = (
    "name, material_class, density_kg_m3, youngs_modulus_gpa, yield_strength_mpa, "
    "cost_usd_per_kg, strength_basis, source, notes, verified"
)


class MaterialDatabase:
    """Create, read, update and delete materials; store analysis history."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._execute_script(_SCHEMA)

    # ---- connection helpers -------------------------------------------------
    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
        except sqlite3.Error as exc:
            raise DatabaseError(f"Cannot open database {self.db_path}: {exc}") from exc
        try:
            yield conn
            conn.commit()
        except sqlite3.IntegrityError:
            conn.rollback()
            raise
        except sqlite3.Error as exc:
            conn.rollback()
            raise DatabaseError(f"Database error: {exc}") from exc
        finally:
            conn.close()

    def _execute_script(self, script: str) -> None:
        with self._connect() as conn:
            conn.executescript(script)

    @staticmethod
    def _row_to_material(row: sqlite3.Row) -> Material:
        return Material(
            id=row["id"], name=row["name"], material_class=row["material_class"],
            density_kg_m3=row["density_kg_m3"], youngs_modulus_gpa=row["youngs_modulus_gpa"],
            yield_strength_mpa=row["yield_strength_mpa"], cost_usd_per_kg=row["cost_usd_per_kg"],
            strength_basis=row["strength_basis"], source=row["source"], notes=row["notes"],
            verified=bool(row["verified"]),
        )

    # ---- materials: read ----------------------------------------------------
    def count(self) -> int:
        with self._connect() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM materials").fetchone()[0])

    def list_materials(self) -> list[Material]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM materials ORDER BY material_class, name").fetchall()
        return [self._row_to_material(r) for r in rows]

    def get(self, material_id: int) -> Material:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM materials WHERE id = ?", (material_id,)).fetchone()
        if row is None:
            raise MaterialNotFoundError(f"No material with id {material_id}.")
        return self._row_to_material(row)

    def to_dataframe(self) -> pd.DataFrame:
        """All materials as a DataFrame keyed by the property keys (Ashby units)."""
        records = [m.to_record() for m in self.list_materials()]
        return pd.DataFrame(records, columns=RECORD_COLUMNS)

    # ---- materials: write -----------------------------------------------------
    def add(self, material: Material) -> Material:
        try:
            with self._connect() as conn:
                cur = conn.execute(
                    f"INSERT INTO materials ({_COLUMNS}) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    self._values(material),
                )
                new_id = cur.lastrowid
        except sqlite3.IntegrityError as exc:
            raise DuplicateMaterialError(f"A material named '{material.name}' already exists.") from exc
        return self.get(new_id)

    def update(self, material_id: int, material: Material) -> Material:
        self.get(material_id)  # raises MaterialNotFoundError
        try:
            with self._connect() as conn:
                conn.execute(
                    "UPDATE materials SET name=?, material_class=?, density_kg_m3=?, "
                    "youngs_modulus_gpa=?, yield_strength_mpa=?, cost_usd_per_kg=?, "
                    "strength_basis=?, source=?, notes=?, verified=? WHERE id=?",
                    (*self._values(material), material_id),
                )
        except sqlite3.IntegrityError as exc:
            raise DuplicateMaterialError(f"A material named '{material.name}' already exists.") from exc
        return self.get(material_id)

    def delete(self, material_id: int) -> None:
        self.get(material_id)
        with self._connect() as conn:
            conn.execute("DELETE FROM materials WHERE id = ?", (material_id,))

    def set_verified(self, material_id: int, verified: bool) -> None:
        self.get(material_id)
        with self._connect() as conn:
            conn.execute("UPDATE materials SET verified = ? WHERE id = ?", (int(verified), material_id))

    @staticmethod
    def _values(m: Material) -> tuple:
        return (m.name, m.material_class, m.density_kg_m3, m.youngs_modulus_gpa,
                m.yield_strength_mpa, m.cost_usd_per_kg, m.strength_basis,
                m.source, m.notes, int(m.verified))

    # ---- seeding --------------------------------------------------------------
    def seed_from_json(self, json_path: str | Path, replace: bool = False) -> int:
        """Load materials from a JSON list. Returns how many rows were inserted.

        With ``replace=True`` the materials table is emptied first (history is kept).
        Existing names are skipped when ``replace=False`` so seeding is idempotent.
        """
        path = Path(json_path)
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise DatabaseError(f"Seed file not found: {path}") from exc
        except json.JSONDecodeError as exc:
            raise DatabaseError(f"Seed file is not valid JSON: {exc}") from exc
        if not isinstance(raw, list):
            raise ValidationError("Seed file must contain a JSON list of materials.")
        materials = [Material.from_dict(item) for item in raw]  # validates every row first
        if replace:
            with self._connect() as conn:
                conn.execute("DELETE FROM materials")
        inserted = 0
        for material in materials:
            try:
                self.add(material)
                inserted += 1
            except DuplicateMaterialError:
                continue
        return inserted
