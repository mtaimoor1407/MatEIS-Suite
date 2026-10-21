"""Binary phase diagram model (Theme 1).

A diagram is a *tiling* of the composition–temperature rectangle by polygons,
one per phase field. Everything else follows from that one idea:

* "Which phase field is the point (X, T) in?"   -> point-in-polygon test
* "Where are the tie-line ends?"                -> intersect the polygon with the
  horizontal line at T; the leftmost and rightmost crossings are the boundary
  compositions of the two coexisting phases
* "How much of each phase?"                     -> lever rule on those ends

Composition X is the weight percent of component B (the right-hand component).
Temperatures are in °C.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from core.exceptions import ValidationError

Point = tuple[float, float]  # (composition wt% B, temperature °C)
EPS = 1e-9


# ---------------------------------------------------------------------------- geometry
def polygon_area(poly: tuple[Point, ...]) -> float:
    """Unsigned area (shoelace formula)."""
    total = 0.0
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1], strict=True):
        total += x1 * y2 - x2 * y1
    return abs(total) / 2.0


def polygon_centroid(poly: tuple[Point, ...]) -> Point:
    """Area centroid; falls back to the vertex mean for degenerate polygons."""
    a = cx = cy = 0.0
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1], strict=True):
        cross = x1 * y2 - x2 * y1
        a += cross
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross
    if abs(a) < EPS:
        return (sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))
    return (cx / (3 * a), cy / (3 * a))


def point_in_polygon(x: float, y: float, poly: tuple[Point, ...], tol: float = 1e-9) -> bool:
    """Ray-casting test. Points on an edge count as inside."""
    inside = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1], strict=True):
        cross = (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)
        if abs(cross) <= tol * max(1.0, abs(x2 - x1) + abs(y2 - y1)) and \
                min(x1, x2) - tol <= x <= max(x1, x2) + tol and min(y1, y2) - tol <= y <= max(y1, y2) + tol:
            return True
        if (y1 > y) != (y2 > y):
            x_int = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < x_int:
                inside = not inside
    return inside


def horizontal_crossings(poly: tuple[Point, ...], temperature: float) -> list[float]:
    """Composition of every crossing of the polygon boundary with the line T = temperature."""
    xs = []
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1], strict=True):
        if abs(y2 - y1) < EPS:
            continue  # horizontal edge: its end points appear in the neighbouring edges
        lo, hi = min(y1, y2), max(y1, y2)
        if lo - EPS <= temperature <= hi + EPS:
            xs.append(x1 + (temperature - y1) * (x2 - x1) / (y2 - y1))
    return xs


# ---------------------------------------------------------------------------- data classes
@dataclass(frozen=True)
class Region:
    """One phase field. ``phases`` are ordered left to right on the tie-line."""

    name: str
    phases: tuple[str, ...]
    polygon: tuple[Point, ...]
    color: str
    label_xy: Point | None = None

    @property
    def is_single_phase(self) -> bool:
        return len(self.phases) == 1

    @property
    def label_position(self) -> Point:
        return self.label_xy or polygon_centroid(self.polygon)


@dataclass(frozen=True)
class Invariant:
    """A horizontal three-phase reaction line (eutectic, eutectoid, peritectic)."""

    name: str
    reaction: str
    temperature: float
    x_left: float
    x_mid: float
    x_right: float


@dataclass(frozen=True)
class PhaseFraction:
    phase: str
    composition: float      # wt% B in that phase
    fraction: float         # mass fraction of the whole sample (0..1)


@dataclass
class Equilibrium:
    """Result of evaluating the diagram at one (X, T)."""

    diagram_key: str
    x: float
    temperature: float
    region: Region
    phases: list[PhaseFraction]
    tie_line: tuple[float, float] | None
    formulas: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    effective_temperature: float | None = None  # set when T was nudged off an invariant line

    @property
    def is_single_phase(self) -> bool:
        return self.region.is_single_phase


# ---------------------------------------------------------------------------- the diagram
class PhaseDiagram:
    """Binary equilibrium diagram with lever-rule evaluation."""

    def __init__(self, key: str, title: str, component_a: str, component_b: str, x_unit: str,
                 x_range: tuple[float, float], t_range: tuple[float, float],
                 regions: list[Region], invariants: list[Invariant],
                 lines: list[tuple[str, tuple[Point, ...]]], source: str, notes: str = "",
                 melting_a: float | None = None, melting_b: float | None = None,
                 phase_names: dict[str, str] | None = None):
        self.key, self.title = key, title
        self.component_a, self.component_b = component_a, component_b
        self.x_unit = x_unit
        self.x_range, self.t_range = x_range, t_range
        self.regions, self.invariants, self.lines = regions, invariants, lines
        self.source, self.notes = source, notes
        self.melting_a, self.melting_b = melting_a, melting_b
        self.phase_names = phase_names or {}
        names = [r.name for r in self.regions]
        if len(names) != len(set(names)):
            raise ValidationError(f"{self.key}: duplicate region names.")

    def phase_label(self, phase: str) -> str:
        return self.phase_names.get(phase, phase)

    # ---- validation ---------------------------------------------------------
    @property
    def x_label(self) -> str:
        return f"Composition (wt% {self.component_b})"

    def validate_point(self, x: float, temperature: float) -> None:
        for label, v in (("Composition", x), ("Temperature", temperature)):
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
                raise ValidationError(f"{label} must be a finite number.")
        (x_lo, x_hi), (t_lo, t_hi) = self.x_range, self.t_range
        if not x_lo <= x <= x_hi:
            raise ValidationError(f"Composition must be between {x_lo:g} and {x_hi:g} wt% {self.component_b} (got {x:g}).")
        if not t_lo <= temperature <= t_hi:
            raise ValidationError(f"Temperature must be between {t_lo:g} and {t_hi:g} °C (got {temperature:g}).")

    # ---- queries -------------------------------------------------------------
    def locate(self, x: float, temperature: float) -> Region:
        self.validate_point(x, temperature)
        for region in self.regions:
            if point_in_polygon(x, temperature, region.polygon):
                return region
        raise ValidationError("The point is not inside any phase field (check the diagram data).")  # pragma: no cover

    def tie_line(self, region: Region, temperature: float) -> tuple[float, float]:
        xs = horizontal_crossings(region.polygon, temperature)
        if len(xs) < 2:
            raise ValidationError("No tie-line at this temperature.")  # pragma: no cover
        return min(xs), max(xs)

    def invariant_at(self, x: float, temperature: float) -> Invariant | None:
        for inv in self.invariants:
            if abs(temperature - inv.temperature) < 1e-6 and inv.x_left - EPS <= x <= inv.x_right + EPS:
                return inv
        return None

    def equilibrium(self, x: float, temperature: float) -> Equilibrium:
        """Phases, their compositions and mass fractions at (X, T)."""
        self.validate_point(x, temperature)
        notes: list[str] = []
        effective = None
        inv = self.invariant_at(x, temperature)
        if inv is not None:
            effective = temperature - 0.01
            notes.append(
                f"T = {temperature:g} °C is exactly on the {inv.name.lower()} line ({inv.reaction}). "
                "Three phases coexist there, so the lever rule is applied just below the line (equilibrium after the reaction).")
        t_eval = effective if effective is not None else temperature
        t_eval = max(t_eval, self.t_range[0])
        region = self.locate(x, t_eval)
        if region.is_single_phase:
            phases = [PhaseFraction(region.phases[0], x, 1.0)]
            return Equilibrium(self.key, x, temperature, region, phases, None,
                               [f"Single phase field: the whole alloy is {region.phases[0]} (100 wt%) with composition C₀ = {x:g} wt% {self.component_b}."],
                               notes, effective)
        x_left, x_right = self.tie_line(region, t_eval)
        width = x_right - x_left
        left, right = region.phases[0], region.phases[1]
        if width < EPS:  # pragma: no cover  (degenerate apex of a field)
            phases = [PhaseFraction(left, x_left, 1.0), PhaseFraction(right, x_right, 0.0)]
            return Equilibrium(self.key, x, temperature, region, phases, (x_left, x_right), [], notes, effective)
        w_left = min(1.0, max(0.0, (x_right - x) / width))
        w_right = 1.0 - w_left
        phases = [PhaseFraction(left, x_left, w_left), PhaseFraction(right, x_right, w_right)]
        c0 = f"{x:g}"
        formulas = [
            f"Tie-line at {t_eval if effective is None else temperature:g} °C: C({left}) = {x_left:.4g}, C({right}) = {x_right:.4g} wt% {self.component_b}",
            f"W({left}) = (C({right}) − C₀) / (C({right}) − C({left})) = ({x_right:.4g} − {c0}) / ({x_right:.4g} − {x_left:.4g}) = {w_left:.4f}",
            f"W({right}) = (C₀ − C({left})) / (C({right}) − C({left})) = ({c0} − {x_left:.4g}) / ({x_right:.4g} − {x_left:.4g}) = {w_right:.4f}",
        ]
        return Equilibrium(self.key, x, temperature, region, phases, (x_left, x_right), formulas, notes, effective)

    # ---- helpers ---------------------------------------------------------------------
    def region_by_name(self, name: str) -> Region:
        for r in self.regions:
            if r.name == name:
                return r
        raise ValidationError(f"No region called '{name}'.")

    def total_area(self) -> float:
        return sum(polygon_area(r.polygon) for r in self.regions)

    def bounding_area(self) -> float:
        return (self.x_range[1] - self.x_range[0]) * (self.t_range[1] - self.t_range[0])
