"""History of saved analyses for all three themes (SQLite).

One table, one row per saved analysis. Inputs and results are stored as JSON so
every theme can save whatever it needs without changing the schema.
"""
from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from core.exceptions import DatabaseError, MaterialNotFoundError, ValidationError

THEMES = ("phase", "selection", "corrosion")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  TEXT NOT NULL,
    theme       TEXT NOT NULL,
    title       TEXT NOT NULL,
    inputs      TEXT NOT NULL,
    results     TEXT NOT NULL
);
"""


class HistoryStore:
    """Add, list, read and delete saved analyses."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
        except sqlite3.Error as exc:
            raise DatabaseError(f"Cannot open database {self.db_path}: {exc}") from exc
        try:
            yield conn
            conn.commit()
        except sqlite3.Error as exc:
            conn.rollback()
            raise DatabaseError(f"Database error: {exc}") from exc
        finally:
            conn.close()

    @staticmethod
    def _row(row: sqlite3.Row) -> dict[str, Any]:
        return {"id": row["id"], "created_at": row["created_at"], "theme": row["theme"],
                "title": row["title"], "inputs": json.loads(row["inputs"]),
                "results": json.loads(row["results"])}

    def add(self, theme: str, title: str, inputs: dict, results: dict) -> int:
        if theme not in THEMES:
            raise ValidationError(f"Unknown theme '{theme}'.")
        if not str(title).strip():
            raise ValidationError("A history entry needs a title.")
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO history (created_at, theme, title, inputs, results) VALUES (?,?,?,?,?)",
                (datetime.now().isoformat(timespec="seconds"), theme, str(title).strip(),
                 json.dumps(inputs, default=str, sort_keys=True), json.dumps(results, default=str, sort_keys=True)))
            return int(cur.lastrowid)

    def list(self, theme: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
        query, params = "SELECT * FROM history", []
        if theme:
            query += " WHERE theme = ?"
            params.append(theme)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(int(limit))
        with self._connect() as conn:
            return [self._row(r) for r in conn.execute(query, params).fetchall()]

    def get(self, entry_id: int) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM history WHERE id = ?", (entry_id,)).fetchone()
        if row is None:
            raise MaterialNotFoundError(f"No history entry with id {entry_id}.")
        return self._row(row)

    def delete(self, entry_id: int) -> None:
        self.get(entry_id)
        with self._connect() as conn:
            conn.execute("DELETE FROM history WHERE id = ?", (entry_id,))

    def clear(self, theme: str | None = None) -> None:
        with self._connect() as conn:
            if theme:
                conn.execute("DELETE FROM history WHERE theme = ?", (theme,))
            else:
                conn.execute("DELETE FROM history")

    def count(self) -> int:
        with self._connect() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM history").fetchone()[0])
