"""Shared definitions: property keys, units, labels, material classes, colours.

Every other module refers to properties by the *keys* below, so a unit or label
is changed in exactly one place.

Units used for calculation and plotting (the Ashby convention):
    density    Mg/m^3   (numerically equal to g/cm^3)
    modulus    GPa      (Young's modulus)
    strength   MPa      (yield strength; see ``strength_basis`` for ceramics etc.)
    cost       USD/kg
    cost_vol   USD/L    (= cost x density, i.e. cost per unit volume)
"""
from dataclasses import dataclass

MATERIAL_CLASSES = ("Metal", "Polymer", "Ceramic", "Composite")
STRENGTH_BASES = ("yield", "tensile", "flexural")

CLASS_COLORS = {
    "Metal": "#3F6C9E",
    "Polymer": "#2F9E6E",
    "Ceramic": "#C98A2B",
    "Composite": "#8E5AA8",
}
EXCLUDED_COLOR = "#C4C9CF"
WINNER_COLOR = "#D12F2F"


@dataclass(frozen=True)
class Property:
    key: str
    label: str
    unit: str
    symbol: str

    @property
    def axis_label(self) -> str:
        return f"{self.label} ({self.unit})"


PROPERTIES = {
    "density": Property("density", "Density", "Mg/m³", "ρ"),
    "modulus": Property("modulus", "Young's modulus", "GPa", "E"),
    "strength": Property("strength", "Yield strength", "MPa", "σy"),
    "cost": Property("cost", "Cost per kg", "USD/kg", "Cm"),
    "cost_vol": Property("cost_vol", "Cost per volume", "USD/L", "Cv"),
}

# Properties the user may filter on (cost_vol is derived but filterable too).
FILTERABLE = tuple(PROPERTIES)


def axis_label(key: str) -> str:
    return PROPERTIES[key].axis_label
