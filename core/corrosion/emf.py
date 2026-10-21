"""EMF / galvanic series database (SQLite) and galvanic-couple risk assessment.

Two series are stored:
  * ``standard``  – standard electrode potentials vs SHE (the textbook "EMF series")
  * ``seawater``  – practical galvanic series in flowing seawater vs SCE; includes alloys
                    and passive films, so it predicts real couples better.
Users can add, edit and delete entries; seeded entries can be restored.
"""
from __future__ import annotations

import json
import math
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

from core.exceptions import DatabaseError, DuplicateMaterialError, MaterialNotFoundError, ValidationError

SERIES = {"standard": "EMF series (V vs SHE)", "seawater": "Galvanic series in seawater (V vs SCE)"}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS emf_series (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL,
    half_reaction  TEXT NOT NULL DEFAULT '',
    potential_v    REAL NOT NULL CHECK (potential_v BETWEEN -4.0 AND 3.0),
    series         TEXT NOT NULL CHECK (series IN ('standard','seawater')),
    source         TEXT NOT NULL DEFAULT '',
    notes          TEXT NOT NULL DEFAULT '',
    custom         INTEGER NOT NULL DEFAULT 0,
    UNIQUE (name, series)
);
"""


@dataclass(frozen=True)
class Electrode:
    name: str
    potential_v: float
    series: str = "standard"
    half_reaction: str = ""
    source: str = ""
    notes: str = ""
    custom: bool = False
    id: int | None = None

    def __post_init__(self) -> None:
        name = str(self.name or "").strip()
        if not name:
            raise ValidationError("Metal name cannot be empty.")
        if self.series not in SERIES:
            raise ValidationError(f"Series must be one of {', '.join(SERIES)}.")
        if isinstance(self.potential_v, bool):
            raise ValidationError("Potential must be a number.")
        try:
            pot = float(self.potential_v)
        except (TypeError, ValueError):
            raise ValidationError(f"Potential must be a number (got {self.potential_v!r}).") from None
        if not math.isfinite(pot) or not -4.0 <= pot <= 3.0:
            raise ValidationError("Potential must be between −4.0 V and +3.0 V.")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "potential_v", pot)


class EMFDatabase:
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
        except sqlite3.IntegrityError:
            conn.rollback()
            raise
        except sqlite3.Error as exc:
            conn.rollback()
            raise DatabaseError(f"Database error: {exc}") from exc
        finally:
            conn.close()

    @staticmethod
    def _row(r: sqlite3.Row) -> Electrode:
        return Electrode(r["name"], r["potential_v"], r["series"], r["half_reaction"], r["source"], r["notes"],
                         bool(r["custom"]), r["id"])

    def count(self, series: str | None = None) -> int:
        with self._connect() as conn:
            if series:
                return int(conn.execute("SELECT COUNT(*) FROM emf_series WHERE series=?", (series,)).fetchone()[0])
            return int(conn.execute("SELECT COUNT(*) FROM emf_series").fetchone()[0])

    def list(self, series: str = "standard") -> list[Electrode]:
        """Entries of one series, most active (most negative) first."""
        if series not in SERIES:
            raise ValidationError(f"Unknown series '{series}'.")
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM emf_series WHERE series=? ORDER BY potential_v, name", (series,)).fetchall()
        return [self._row(r) for r in rows]

    def get(self, entry_id: int) -> Electrode:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM emf_series WHERE id=?", (entry_id,)).fetchone()
        if row is None:
            raise MaterialNotFoundError(f"No entry with id {entry_id}.")
        return self._row(row)

    def find(self, name: str, series: str) -> Electrode:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM emf_series WHERE name=? AND series=?", (name, series)).fetchone()
        if row is None:
            raise MaterialNotFoundError(f"'{name}' is not in the {series} series.")
        return self._row(row)

    def add(self, e: Electrode) -> Electrode:
        try:
            with self._connect() as conn:
                cur = conn.execute(
                    "INSERT INTO emf_series (name, half_reaction, potential_v, series, source, notes, custom) VALUES (?,?,?,?,?,?,?)",
                    (e.name, e.half_reaction, e.potential_v, e.series, e.source, e.notes, int(e.custom)))
                new_id = cur.lastrowid
        except sqlite3.IntegrityError as exc:
            raise DuplicateMaterialError(f"'{e.name}' already exists in the {e.series} series.") from exc
        return self.get(new_id)

    def update(self, entry_id: int, e: Electrode) -> Electrode:
        self.get(entry_id)
        try:
            with self._connect() as conn:
                conn.execute("UPDATE emf_series SET name=?, half_reaction=?, potential_v=?, series=?, source=?, notes=? WHERE id=?",
                             (e.name, e.half_reaction, e.potential_v, e.series, e.source, e.notes, entry_id))
        except sqlite3.IntegrityError as exc:
            raise DuplicateMaterialError(f"'{e.name}' already exists in the {e.series} series.") from exc
        return self.get(entry_id)

    def delete(self, entry_id: int) -> None:
        self.get(entry_id)
        with self._connect() as conn:
            conn.execute("DELETE FROM emf_series WHERE id=?", (entry_id,))

    def seed_from_json(self, path: str | Path, replace: bool = False) -> int:
        try:
            raw = json.loads(Path(path).read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise DatabaseError(f"Seed file not found: {path}") from exc
        except json.JSONDecodeError as exc:
            raise DatabaseError(f"Seed file is not valid JSON: {exc}") from exc
        if not isinstance(raw, list):
            raise ValidationError("EMF seed file must contain a JSON list.")
        entries = [Electrode(**{k: v for k, v in item.items() if k in Electrode.__dataclass_fields__}) for item in raw]
        if replace:
            with self._connect() as conn:
                conn.execute("DELETE FROM emf_series")
        n = 0
        for e in entries:
            try:
                self.add(e)
                n += 1
            except DuplicateMaterialError:
                continue
        return n


ENVIRONMENT_FACTORS = {  # how strongly the electrolyte supports galvanic current (added to the risk score)
    "Indoor dry atmosphere": -1.0,
    "Rural atmosphere": 0.0,
    "Urban / industrial atmosphere": 0.5,
    "Marine atmosphere (coastal)": 1.0,
    "Freshwater immersion": 0.5,
    "Buried in soil": 0.5,
    "Seawater immersion": 1.5,
    "Acidic / chemical process": 1.5,
}
LEVELS = [(0.75, "Negligible", "#2FBF71"), (1.75, "Low", "#C8D655"), (2.75, "Moderate", "#F2C14E"),
          (3.75, "High", "#EF8354"), (math.inf, "Severe", "#E4572E")]


def risk_level(score: float) -> tuple[str, str]:
    for limit, name, color in LEVELS:
        if score < limit:
            return name, color
    return LEVELS[-1][1:]  # pragma: no cover


@dataclass
class GalvanicAssessment:
    anode: Electrode
    cathode: Electrode
    delta_e: float
    area_ratio: float
    environment: str
    score: float
    level: str
    color: str
    components: dict = field(default_factory=dict)
    explanation: list[str] = field(default_factory=list)
    mitigations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"anode": self.anode.name, "cathode": self.cathode.name, "delta_e_v": self.delta_e,
                "series": self.anode.series, "area_ratio_cathode_to_anode": self.area_ratio,
                "environment": self.environment, "score": self.score, "level": self.level}


def assess_couple(a: Electrode, b: Electrode, area_ratio: float = 1.0,
                  environment: str = "Seawater immersion") -> GalvanicAssessment:
    """Rate the risk of galvanic corrosion for metals ``a`` and ``b`` in electrical contact.

    ``area_ratio`` = cathode area / anode area. A small anode with a large cathode is the
    worst case: all the cathodic current is drawn from a small area.
    """
    if a.series != b.series:
        raise ValidationError("Both metals must come from the same series (their potentials use different references).")
    if a.name == b.name:
        raise ValidationError("Choose two different metals.")
    if environment not in ENVIRONMENT_FACTORS:
        raise ValidationError(f"Unknown environment '{environment}'.")
    if isinstance(area_ratio, bool) or not isinstance(area_ratio, (int, float)) or not math.isfinite(area_ratio) or area_ratio <= 0:
        raise ValidationError("Area ratio must be a positive number.")
    anode, cathode = (a, b) if a.potential_v < b.potential_v else (b, a)
    de = cathode.potential_v - anode.potential_v
    base = min(de / 0.15, 4.5)
    env = ENVIRONMENT_FACTORS[environment]
    area = max(-1.0, min(1.5, math.log10(area_ratio)))
    score = max(0.0, base + env + area)
    level, color = risk_level(score)
    expl = [f"{anode.name} is less noble (E = {anode.potential_v:+.2f} V) than {cathode.name} (E = {cathode.potential_v:+.2f} V), so {anode.name} is the anode and corrodes faster when the two are connected.",
            f"Potential difference ΔE = {de:.2f} V.",
            f"Environment: {environment} (factor {env:+.1f}). Area ratio cathode : anode = {area_ratio:g} (factor {area:+.1f})."]
    if area_ratio > 5:
        expl.append("The cathode is much larger than the anode, so the anode area carries a high current density: this is the unfavourable case.")
    elif area_ratio < 0.5:
        expl.append("The anode is much larger than the cathode, so the attack is spread over a large area: this is the favourable case.")
    mit = []
    if level in ("Moderate", "High", "Severe"):
        mit += ["Electrically isolate the metals (insulating washers, sleeves or gaskets) so no current path exists.",
                "Coat the more noble metal (the cathode). Never coat only the anode: a pinhole would create a tiny anode and a huge cathode.",
                f"Keep the anode ({anode.name}) as the larger part, or make fasteners from the nobler metal.",
                "Keep the joint dry: seal crevices and provide drainage."]
    if level in ("High", "Severe"):
        mit += ["Choose a closer pair of metals (look for ΔE below 0.15 V) or replace one of them.",
                f"Use a sacrificial anode (e.g. zinc or magnesium) that is more active than {anode.name}."]
    if level in ("Negligible", "Low"):
        mit.append("No special measures needed; inspect at routine intervals.")
    return GalvanicAssessment(anode, cathode, de, float(area_ratio), environment, score, level, color,
                              {"base": base, "environment": env, "area": area}, expl, mit)


def delta_matrix(electrodes: list[Electrode]) -> list[list[float]]:
    """Matrix of |ΔE| between every pair (same series only)."""
    if len({e.series for e in electrodes}) > 1:
        raise ValidationError("All metals must come from the same series.")
    return [[abs(a.potential_v - b.potential_v) for b in electrodes] for a in electrodes]
