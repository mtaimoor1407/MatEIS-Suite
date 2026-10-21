"""Design-constraint filtering, e.g. "yield strength >= 200 MPa"."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import pandas as pd

from core.exceptions import ValidationError
from core.selection.properties import FILTERABLE, MATERIAL_CLASSES, PROPERTIES

Bound = float | None


@dataclass
class Constraints:
    """User-chosen limits. ``None`` means "no limit". Bounds are inclusive."""

    classes: tuple[str, ...] = MATERIAL_CLASSES
    ranges: dict[str, tuple[Bound, Bound]] = field(default_factory=dict)

    def validate(self) -> Constraints:
        if not self.classes:
            raise ValidationError("Select at least one material class.")
        unknown = [c for c in self.classes if c not in MATERIAL_CLASSES]
        if unknown:
            raise ValidationError(f"Unknown material class: {', '.join(map(str, unknown))}.")
        for key, bounds in self.ranges.items():
            if key not in FILTERABLE:
                raise ValidationError(f"Cannot filter on unknown property '{key}'.")
            if len(bounds) != 2:
                raise ValidationError(f"Range for {PROPERTIES[key].label} needs a minimum and a maximum.")
            low, high = bounds
            for value in (low, high):
                if value is None:
                    continue
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                    raise ValidationError(f"{PROPERTIES[key].label}: limits must be finite numbers.")
                if value < 0:
                    raise ValidationError(f"{PROPERTIES[key].label}: limits cannot be negative (got {value:g}).")
            if low is not None and high is not None and low > high:
                raise ValidationError(
                    f"{PROPERTIES[key].label}: minimum ({low:g}) is greater than maximum ({high:g})."
                )
        return self

    def describe(self) -> list[str]:
        """Human-readable list used in the PDF report and the history log."""
        lines = [f"Classes: {', '.join(self.classes)}"]
        for key, (low, high) in self.ranges.items():
            prop = PROPERTIES[key]
            if low is not None:
                lines.append(f"{prop.label} ≥ {low:g} {prop.unit}")
            if high is not None:
                lines.append(f"{prop.label} ≤ {high:g} {prop.unit}")
        return lines

    def to_dict(self) -> dict:
        return {"classes": list(self.classes),
                "ranges": {k: list(v) for k, v in self.ranges.items() if v != (None, None)}}


def apply_constraints(df: pd.DataFrame, constraints: Constraints) -> pd.DataFrame:
    """Return the rows of ``df`` that satisfy every constraint (may be empty)."""
    constraints.validate()
    mask = df["material_class"].isin(constraints.classes)
    for key, (low, high) in constraints.ranges.items():
        if low is not None:
            mask &= df[key] >= low
        if high is not None:
            mask &= df[key] <= high
    return df[mask].copy()
