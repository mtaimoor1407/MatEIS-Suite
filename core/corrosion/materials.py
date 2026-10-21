"""Metals and alloys used by the corrosion tools: density, composition, equivalent weight.

Equivalent weight (ASTM G102):   EW = 1 / Σ (n_i · f_i / W_i)
    f_i mass fraction of element i, W_i atomic weight, n_i oxidation state (valence)
It is the mass of the alloy that corrodes per mole of electrons.
"""
from __future__ import annotations

from dataclasses import dataclass

from core.exceptions import ValidationError

ATOMIC_WEIGHT = {"Fe": 55.845, "Cr": 51.996, "Ni": 58.693, "Mn": 54.938, "Mo": 95.95, "Cu": 63.546,
                 "Zn": 65.38, "Al": 26.982, "Mg": 24.305, "Ti": 47.867, "Pb": 207.2, "Sn": 118.71, "Co": 58.933}
DEFAULT_VALENCE = {"Fe": 2, "Cr": 3, "Ni": 2, "Mn": 2, "Mo": 3, "Cu": 2, "Zn": 2, "Al": 3, "Mg": 2,
                   "Ti": 4, "Pb": 2, "Sn": 2, "Co": 2}
FARADAY = 96485.33  # C/mol


def equivalent_weight(composition: dict[str, float], valence: dict[str, int] | None = None) -> float:
    """EW of an alloy from mass fractions (they are normalised, so they need not sum to exactly 1)."""
    if not composition:
        raise ValidationError("Composition cannot be empty.")
    valence = {**DEFAULT_VALENCE, **(valence or {})}
    total = 0.0
    for element, fraction in composition.items():
        if element not in ATOMIC_WEIGHT:
            raise ValidationError(f"Unknown element '{element}'.")
        if not isinstance(fraction, (int, float)) or fraction < 0:
            raise ValidationError(f"Mass fraction of {element} must be a non-negative number.")
        total += fraction
    if total <= 0:
        raise ValidationError("Mass fractions must add up to more than zero.")
    s = sum((valence[e] * f / total) / ATOMIC_WEIGHT[e] for e, f in composition.items())
    return 1.0 / s


@dataclass(frozen=True)
class CorrosionMaterial:
    key: str
    name: str
    family: str                 # steel | stainless | aluminum | copper | zinc | magnesium | titanium | nickel | lead | tin
    density: float              # g/cm³
    composition: dict
    note: str = ""

    @property
    def equivalent_weight(self) -> float:
        return equivalent_weight(self.composition)


def _m(key, name, family, density, comp, note=""):
    return CorrosionMaterial(key, name, family, density, comp, note)


MATERIALS: dict[str, CorrosionMaterial] = {m.key: m for m in [
    _m("carbon_steel", "Carbon steel (plain)", "steel", 7.85, {"Fe": 1.0}, "EW = 27.92 as in ASTM G102"),
    _m("cast_iron", "Cast iron", "steel", 7.20, {"Fe": 1.0}),
    _m("ss304", "Stainless steel 304", "stainless", 8.00, {"Fe": 0.70, "Cr": 0.19, "Ni": 0.10, "Mn": 0.01}),
    _m("ss316", "Stainless steel 316", "stainless", 8.00, {"Fe": 0.665, "Cr": 0.17, "Ni": 0.12, "Mo": 0.025, "Mn": 0.02}),
    _m("al6061", "Aluminum 6061", "aluminum", 2.70, {"Al": 0.98, "Mg": 0.01}),
    _m("al_pure", "Aluminum (pure)", "aluminum", 2.70, {"Al": 1.0}),
    _m("copper", "Copper", "copper", 8.96, {"Cu": 1.0}),
    _m("brass", "Brass 70Cu-30Zn", "copper", 8.53, {"Cu": 0.70, "Zn": 0.30}),
    _m("zinc", "Zinc", "zinc", 7.14, {"Zn": 1.0}, "also represents hot-dip galvanized coatings"),
    _m("magnesium", "Magnesium alloy AZ31B", "magnesium", 1.77, {"Mg": 0.96, "Al": 0.03, "Zn": 0.01}),
    _m("titanium", "Titanium (Ti-6Al-4V approx.)", "titanium", 4.43, {"Ti": 0.94, "Al": 0.06}),
    _m("nickel", "Nickel", "nickel", 8.91, {"Ni": 1.0}),
    _m("inconel625", "Inconel 625 (approx.)", "nickel", 8.44, {"Ni": 0.62, "Cr": 0.22, "Mo": 0.09, "Fe": 0.05}),
    _m("lead", "Lead", "lead", 11.34, {"Pb": 1.0}),
    _m("tin", "Tin", "tin", 7.31, {"Sn": 1.0}),
]}


def get_material(key: str) -> CorrosionMaterial:
    try:
        return MATERIALS[key]
    except KeyError:
        raise ValidationError(f"Unknown corrosion material '{key}'.") from None
