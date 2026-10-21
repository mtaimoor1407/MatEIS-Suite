"""The Material entity: one row of the database, validated on construction."""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, fields
from typing import Any

from core.exceptions import ValidationError
from core.selection.properties import MATERIAL_CLASSES, STRENGTH_BASES

# Physically plausible upper limits. They catch typos such as a density entered
# in kg/m^3 where Mg/m^3 was meant, or a modulus entered in Pa instead of GPa.
LIMITS = {
    "density_kg_m3": (1.0, 25_000.0),          # osmium is ~22,600
    "youngs_modulus_gpa": (0.001, 1_500.0),    # diamond is ~1,200
    "yield_strength_mpa": (0.1, 20_000.0),     # best fibres/whiskers
    "cost_usd_per_kg": (0.001, 100_000.0),
}
LABELS = {
    "density_kg_m3": "Density (kg/m³)",
    "youngs_modulus_gpa": "Young's modulus (GPa)",
    "yield_strength_mpa": "Strength (MPa)",
    "cost_usd_per_kg": "Cost (USD/kg)",
}


def _as_number(field_name: str, value: Any) -> float:
    if isinstance(value, bool):
        raise ValidationError(f"{LABELS[field_name]} must be a number, not True/False.")
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{LABELS[field_name]} must be a number (got {value!r}).") from None
    if not math.isfinite(number):
        raise ValidationError(f"{LABELS[field_name]} must be a finite number.")
    low, high = LIMITS[field_name]
    if not low <= number <= high:
        raise ValidationError(
            f"{LABELS[field_name]} must be between {low:g} and {high:g} (got {number:g})."
        )
    return number


@dataclass(frozen=True)
class Material:
    name: str
    material_class: str
    density_kg_m3: float
    youngs_modulus_gpa: float
    yield_strength_mpa: float
    cost_usd_per_kg: float
    strength_basis: str = "yield"
    source: str = ""
    notes: str = ""
    verified: bool = False
    id: int | None = None

    def __post_init__(self) -> None:
        name = str(self.name).strip() if self.name is not None else ""
        if not name:
            raise ValidationError("Material name cannot be empty.")
        if self.material_class not in MATERIAL_CLASSES:
            raise ValidationError(
                f"Material class must be one of {', '.join(MATERIAL_CLASSES)} (got {self.material_class!r})."
            )
        if self.strength_basis not in STRENGTH_BASES:
            raise ValidationError(
                f"Strength basis must be one of {', '.join(STRENGTH_BASES)} (got {self.strength_basis!r})."
            )
        # frozen dataclass: assign through object.__setattr__
        object.__setattr__(self, "name", name)
        for field_name in LIMITS:
            object.__setattr__(self, field_name, _as_number(field_name, getattr(self, field_name)))
        object.__setattr__(self, "source", str(self.source or "").strip())
        object.__setattr__(self, "notes", str(self.notes or "").strip())
        object.__setattr__(self, "verified", bool(self.verified))

    # ---- derived quantities (Ashby units) ---------------------------------
    @property
    def density_mg_m3(self) -> float:
        return self.density_kg_m3 / 1000.0

    @property
    def cost_per_volume(self) -> float:
        """USD per litre of material: cost per kg x density in kg/L."""
        return self.cost_usd_per_kg * self.density_mg_m3

    # ---- conversion --------------------------------------------------------
    def to_record(self) -> dict[str, Any]:
        """Flat dict keyed by the property keys used in DataFrames and charts."""
        return {
            "id": self.id,
            "name": self.name,
            "material_class": self.material_class,
            "density": self.density_mg_m3,
            "modulus": self.youngs_modulus_gpa,
            "strength": self.yield_strength_mpa,
            "cost": self.cost_usd_per_kg,
            "cost_vol": self.cost_per_volume,
            "strength_basis": self.strength_basis,
            "source": self.source,
            "verified": self.verified,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Material:
        """Build from a dict (JSON seed or form), ignoring unknown keys."""
        allowed = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in allowed})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
