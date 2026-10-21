"""Ashby performance indices and ranking.

A performance index M combines properties so that *bigger M is always better*
for a given design objective. Every index here has the form

        M = (numerator property) ^ p / (denominator property)

with the numerator being modulus E or strength σy, and the denominator being
density ρ (minimise mass) or cost per volume Cv (minimise cost).

Derivations (Ashby, *Materials Selection in Mechanical Design*):
    stiff tie     E/ρ        stiff beam    E^(1/2)/ρ     stiff plate   E^(1/3)/ρ
    strong tie    σy/ρ       strong beam   σy^(2/3)/ρ    strong plate  σy^(1/2)/ρ
Replacing ρ with Cv = Cm·ρ gives the minimum-cost version of each.

On a log-log chart of numerator vs denominator, lines of constant M have slope
1/p, so the "guide line" for an index can be drawn straight through a material.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

import numpy as np
import pandas as pd

from core.exceptions import ValidationError
from core.selection.properties import PROPERTIES

_EXPONENT_TEXT = {Fraction(1): "", Fraction(1, 2): "^½", Fraction(1, 3): "^⅓", Fraction(2, 3): "^⅔"}


@dataclass(frozen=True)
class PerformanceIndex:
    key: str
    label: str
    numerator: str       # property key: "modulus" or "strength"
    exponent: Fraction   # p
    denominator: str     # property key: "density" or "cost_vol"
    use_case: str

    @property
    def formula(self) -> str:
        num = PROPERTIES[self.numerator].symbol + _EXPONENT_TEXT[self.exponent]
        den = PROPERTIES[self.denominator].symbol
        return f"{num} / {den}"

    @property
    def unit(self) -> str:
        num_unit = PROPERTIES[self.numerator].unit
        exp = _EXPONENT_TEXT[self.exponent].replace("^", "")
        num_part = num_unit if not exp else f"{num_unit}^{exp}"
        return f"{num_part} / ({PROPERTIES[self.denominator].unit})"

    @property
    def guide_slope(self) -> float:
        """Slope of constant-M lines on log(numerator) vs log(denominator) axes."""
        return 1.0 / float(self.exponent)

    @property
    def axes(self) -> tuple[str, str]:
        """(x key, y key) of the chart on which this index's guide line is straight."""
        return self.denominator, self.numerator

    def compute(self, df: pd.DataFrame) -> pd.Series:
        num = df[self.numerator].astype(float)
        den = df[self.denominator].astype(float)
        if (den <= 0).any() or (num <= 0).any():
            raise ValidationError("Performance indices need strictly positive property values.")
        return (num ** float(self.exponent)) / den


_E, _S = "modulus", "strength"
_THIRD, _HALF, _TWO_THIRDS, _ONE = Fraction(1, 3), Fraction(1, 2), Fraction(2, 3), Fraction(1)

INDICES: dict[str, PerformanceIndex] = {i.key: i for i in [
    PerformanceIndex("stiff_tie", "Light, stiff tie (rod in tension)", _E, _ONE, "density", "Minimum mass for a given stiffness in tension."),
    PerformanceIndex("stiff_beam", "Light, stiff beam", _E, _HALF, "density", "Minimum mass for a given bending stiffness (beams, shafts)."),
    PerformanceIndex("stiff_plate", "Light, stiff plate / panel", _E, _THIRD, "density", "Minimum mass for a given plate bending stiffness."),
    PerformanceIndex("strong_tie", "Light, strong tie (rod in tension)", _S, _ONE, "density", "Minimum mass for a given tensile load capacity."),
    PerformanceIndex("strong_beam", "Light, strong beam", _S, _TWO_THIRDS, "density", "Minimum mass for a given bending strength."),
    PerformanceIndex("strong_plate", "Light, strong plate / panel", _S, _HALF, "density", "Minimum mass for a given plate bending strength."),
    PerformanceIndex("cheap_stiff_beam", "Cheap, stiff beam", _E, _HALF, "cost_vol", "Minimum cost for a given bending stiffness."),
    PerformanceIndex("cheap_strong_beam", "Cheap, strong beam", _S, _TWO_THIRDS, "cost_vol", "Minimum cost for a given bending strength."),
    PerformanceIndex("cheap_strong_tie", "Cheap, strong tie", _S, _ONE, "cost_vol", "Minimum cost for a given tensile load capacity."),
]}


def get_index(key: str) -> PerformanceIndex:
    try:
        return INDICES[key]
    except KeyError:
        raise ValidationError(f"Unknown performance index '{key}'.") from None


def rank_materials(df: pd.DataFrame, index: PerformanceIndex) -> pd.DataFrame:
    """Add ``index_value`` and ``rank`` (1 = best) and sort best-first."""
    out = df.copy()
    if out.empty:
        out["index_value"] = pd.Series(dtype=float)
        out["rank"] = pd.Series(dtype=int)
        return out
    out["index_value"] = index.compute(out)
    out = out.sort_values("index_value", ascending=False).reset_index(drop=True)
    out["rank"] = np.arange(1, len(out) + 1)
    return out


def guide_line(index: PerformanceIndex, x_ref: float, y_ref: float,
               x_min: float, x_max: float, n: int = 50) -> tuple[np.ndarray, np.ndarray]:
    """Points of the constant-M line passing through (x_ref, y_ref).

    From M = y^p / x:  y = y_ref · (x / x_ref)^(1/p).
    """
    if min(x_ref, y_ref, x_min) <= 0 or x_max <= x_min:
        raise ValidationError("Guide line needs positive coordinates and x_max > x_min.")
    x = np.geomspace(x_min, x_max, n)
    return x, y_ref * (x / x_ref) ** index.guide_slope
