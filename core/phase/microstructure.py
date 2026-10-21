"""Microstructure prediction for slowly cooled alloys.

Phases (what the diagram gives) are not the same as *microconstituents* (what you
see under the microscope). For example, steel below 727 °C contains two phases,
ferrite and cementite, but its microstructure is made of *proeutectoid ferrite*
grains plus *pearlite* (a lamellar mixture of the same two phases).

All fractions are mass fractions and assume slow (equilibrium) cooling.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from core.phase.diagram import Equilibrium, PhaseDiagram

C_EUTECTOID, C_ALPHA_MAX, C_EUTECTIC, C_CEMENTITE, C_GAMMA_MAX = 0.76, 0.022, 4.30, 6.70, 2.14


@dataclass(frozen=True)
class Constituent:
    name: str
    fraction: float
    texture: str          # grains | lamellar | matrix_particles | liquid
    color: str
    color2: str = ""
    note: str = ""


@dataclass
class Microstructure:
    classification: str
    constituents: list[Constituent]
    description: str
    properties: str = ""
    formulas: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


_PHASE_STYLE = {
    "L": ("liquid", "#E4572E"), "δ": ("grains", "#C9D6DF"), "γ": ("grains", "#CFD8C0"),
    "α": ("grains", "#E8ECEF"), "Fe₃C": ("grains", "#F6F3E8"),
}
_PHASE_STYLE_CUNI = {"L": ("liquid", "#E4572E"), "α": ("grains", "#C9A27E")}
_PHASE_STYLE_PBSN = {"L": ("liquid", "#E4572E"), "α": ("grains", "#3C434B"), "β": ("grains", "#D7DBDF")}

_PEARLITE = dict(texture="lamellar", color="#4A525B", color2="#C9D0D6")
_FERRITE = dict(texture="grains", color="#E8ECEF")
_CEMENTITE = dict(texture="grains", color="#F6F3E8")
_LEDEBURITE = dict(texture="matrix_particles", color="#F1EEE6", color2="#4A525B")


def _from_phases(diagram: PhaseDiagram, eq: Equilibrium, styles: dict) -> list[Constituent]:
    out = []
    for p in eq.phases:
        if p.fraction <= 1e-9:
            continue
        texture, color = styles.get(p.phase, ("grains", "#CCCCCC"))
        out.append(Constituent(diagram.phase_label(p.phase), p.fraction, texture, color))
    return out


def _iron_carbon(diagram: PhaseDiagram, eq: Equilibrium) -> Microstructure:
    x = eq.x
    t_eff = eq.effective_temperature if eq.effective_temperature is not None else eq.temperature
    if t_eff >= 727.0:
        names = " + ".join(diagram.phase_label(p.phase) for p in eq.phases)
        desc = f"At {eq.temperature:g} °C the alloy is {names}. The room-temperature microstructure forms on slow cooling through the reactions below."
        if eq.region.name == "α + γ":
            desc = "Ferrite grains (α) nucleate on austenite grain boundaries and grow as the steel cools through the α + γ field."
        elif eq.region.name == "γ":
            desc = "Uniform austenite (γ) grains: the starting point for heat treatment of steels."
        return Microstructure("Above the eutectoid temperature", _from_phases(diagram, eq, _PHASE_STYLE), desc)

    f: list[Constituent] = []
    formulas: list[str] = []
    if x < C_ALPHA_MAX:
        label = "Commercially pure iron (ferrite)"
        f = [Constituent("Ferrite (α)", 1.0, **_FERRITE)]
        desc = "Single-phase ferrite grains. Soft, ductile and magnetic; very low strength."
        props = "Very soft and ductile (e.g. electrical iron, ingot iron)."
    elif x < C_EUTECTOID - 1e-12:
        w_p = (x - C_ALPHA_MAX) / (C_EUTECTOID - C_ALPHA_MAX)
        w_a = (C_EUTECTOID - x) / (C_EUTECTOID - C_ALPHA_MAX)
        label = "Hypoeutectoid steel"
        f = [Constituent("Proeutectoid ferrite", w_a, **_FERRITE), Constituent("Pearlite", w_p, **_PEARLITE)]
        formulas = [f"W(pearlite) = (C₀ − 0.022) / (0.76 − 0.022) = ({x:g} − 0.022) / 0.738 = {w_p:.4f}",
                    f"W(proeutectoid α) = (0.76 − C₀) / (0.76 − 0.022) = (0.76 − {x:g}) / 0.738 = {w_a:.4f}"]
        desc = "Proeutectoid ferrite (light) formed first along the austenite grain boundaries; the remaining austenite transformed to pearlite (dark lamellae)."
        props = "Ductile and tough; strength rises with carbon (low- and medium-carbon steels, structural steel)."
    elif abs(x - C_EUTECTOID) < 1e-12:
        label = "Eutectoid steel"
        f = [Constituent("Pearlite", 1.0, **_PEARLITE)]
        formulas = ["At the eutectoid composition the structure is 100% pearlite."]
        desc = "Fully pearlitic: alternating lamellae of ferrite and cementite formed from austenite at 727 °C."
        props = "Strong and moderately hard (rail steels, wire)."
    elif x <= C_GAMMA_MAX:
        w_p = (C_CEMENTITE - x) / (C_CEMENTITE - C_EUTECTOID)
        w_c = (x - C_EUTECTOID) / (C_CEMENTITE - C_EUTECTOID)
        label = "Hypereutectoid steel"
        f = [Constituent("Proeutectoid cementite", w_c, **_CEMENTITE), Constituent("Pearlite", w_p, **_PEARLITE)]
        formulas = [f"W(pearlite) = (6.70 − C₁) / (6.70 − 0.76) = (6.70 − {x:g}) / 5.94 = {w_p:.4f}",
                    f"W(proeutectoid Fe₃C) = (C₁ − 0.76) / (6.70 − 0.76) = ({x:g} − 0.76) / 5.94 = {w_c:.4f}"]
        desc = "A network of proeutectoid cementite (bright) outlines the former austenite grains; the grains themselves are pearlite."
        props = "Very hard and wear-resistant but brittle (tool steels, bearings)."
    elif x < C_EUTECTIC - 1e-12:
        w_g = (C_EUTECTIC - x) / (C_EUTECTIC - C_GAMMA_MAX)
        w_l = (x - C_GAMMA_MAX) / (C_EUTECTIC - C_GAMMA_MAX)
        label = "Hypoeutectic white cast iron"
        f = [Constituent("Pearlite + secondary Fe₃C (from primary γ)", w_g, **_PEARLITE),
             Constituent("Transformed ledeburite", w_l, **_LEDEBURITE)]
        formulas = [f"W(primary γ) = (4.30 − C₀) / (4.30 − 2.14) = (4.30 − {x:g}) / 2.16 = {w_g:.4f}",
                    f"W(ledeburite) = (C₀ − 2.14) / (4.30 − 2.14) = ({x:g} − 2.14) / 2.16 = {w_l:.4f}"]
        desc = "Primary austenite dendrites (now pearlite) in a matrix of ledeburite, a eutectic of cementite and austenite that has transformed on cooling."
        props = "Extremely hard and brittle; white cast iron for wear surfaces."
    elif abs(x - C_EUTECTIC) < 1e-12:
        label = "Eutectic white cast iron"
        f = [Constituent("Transformed ledeburite", 1.0, **_LEDEBURITE)]
        formulas = ["At the eutectic composition the structure is 100% ledeburite."]
        desc = "Entirely ledeburite: pearlite islands in a cementite matrix."
        props = "Extremely hard and brittle."
    else:
        w_c = (x - C_EUTECTIC) / (C_CEMENTITE - C_EUTECTIC)
        w_l = (C_CEMENTITE - x) / (C_CEMENTITE - C_EUTECTIC)
        label = "Hypereutectic white cast iron"
        f = [Constituent("Primary cementite", w_c, **_CEMENTITE), Constituent("Transformed ledeburite", w_l, **_LEDEBURITE)]
        formulas = [f"W(primary Fe₃C) = (C₀ − 4.30) / (6.70 − 4.30) = ({x:g} − 4.30) / 2.40 = {w_c:.4f}",
                    f"W(ledeburite) = (6.70 − C₀) / (6.70 − 4.30) = (6.70 − {x:g}) / 2.40 = {w_l:.4f}"]
        desc = "Large primary cementite plates (bright) in a ledeburite matrix."
        props = "Extremely hard and brittle; rarely used."
    notes = ["Fractions are for slow cooling to just below 727 °C. Phase amounts (ferrite and cementite) come from the lever rule above."]
    return Microstructure(label, f, desc, props, formulas, notes)


def _eutectic_binary(diagram: PhaseDiagram, eq: Equilibrium) -> Microstructure:
    x = eq.x
    t_eff = eq.effective_temperature if eq.effective_temperature is not None else eq.temperature
    inv = diagram.invariants[0]
    if t_eff >= inv.temperature or x <= inv.x_left or x >= inv.x_right:
        names = " + ".join(diagram.phase_label(p.phase) for p in eq.phases)
        if len(eq.phases) == 1 and eq.phases[0].phase == "L":
            desc = "Completely liquid solder bath."
        elif len(eq.phases) == 1:
            desc = f"Single solid phase: {names}."
        else:
            desc = f"Coexisting {names}."
        label = "Solid solution" if len(eq.phases) == 1 and eq.phases[0].phase != "L" else "Equilibrium phases"
        if t_eff < inv.temperature and len(eq.phases) == 2:
            desc = "Solid-solution matrix with fine precipitates of the second phase (solubility falls on cooling)."
        return Microstructure(label, _from_phases(diagram, eq, _PHASE_STYLE_PBSN), desc)
    eutectic = Constituent("Eutectic (α + β lamellae)", 1.0, "lamellar", "#3C434B", "#D7DBDF")
    if abs(x - inv.x_mid) < 1e-12:
        return Microstructure("Eutectic alloy", [eutectic], "Entirely fine lamellar eutectic: α (dark) and β (light) alternate. Melts at a single temperature (183 °C).",
                              "Lowest melting alloy of the system: ideal solder.",
                              ["At the eutectic composition the structure is 100% eutectic."])
    if x < inv.x_mid:
        w_e = (x - inv.x_left) / (inv.x_mid - inv.x_left)
        w_p = 1 - w_e
        formulas = [f"W(eutectic) = (C₀ − 18.3) / (61.9 − 18.3) = ({x:g} − 18.3) / 43.6 = {w_e:.4f}",
                    f"W(primary α) = (61.9 − C₀) / (61.9 − 18.3) = (61.9 − {x:g}) / 43.6 = {w_p:.4f}"]
        cons = [Constituent("Primary (proeutectic) α", w_p, "grains", "#3C434B"), Constituent("Eutectic (α + β lamellae)", w_e, "lamellar", "#3C434B", "#D7DBDF")]
        desc, label = "Large primary α grains (dark) surrounded by fine lamellar eutectic.", "Hypoeutectic alloy"
    else:
        w_e = (inv.x_right - x) / (inv.x_right - inv.x_mid)
        w_p = 1 - w_e
        formulas = [f"W(eutectic) = (97.8 − C₀) / (97.8 − 61.9) = (97.8 − {x:g}) / 35.9 = {w_e:.4f}",
                    f"W(primary β) = (C₀ − 61.9) / (97.8 − 61.9) = ({x:g} − 61.9) / 35.9 = {w_p:.4f}"]
        cons = [Constituent("Primary (proeutectic) β", w_p, "grains", "#D7DBDF"), Constituent("Eutectic (α + β lamellae)", w_e, "lamellar", "#3C434B", "#D7DBDF")]
        desc, label = "Large primary β grains (light) surrounded by fine lamellar eutectic.", "Hypereutectic alloy"
    return Microstructure(label, cons, desc, "A pasty (mushy) range exists between the liquidus and the eutectic line.", formulas,
                          ["Microconstituent fractions are evaluated at the eutectic temperature (just above 183 °C); phase amounts at the chosen T are given by the lever rule."])


def _isomorphous(diagram: PhaseDiagram, eq: Equilibrium) -> Microstructure:
    cons = _from_phases(diagram, eq, _PHASE_STYLE_CUNI)
    if eq.region.name == "L":
        return Microstructure("Liquid", cons, "Molten Cu–Ni solution; no crystals yet.")
    if eq.region.name == "α":
        return Microstructure(
            "Single-phase solid solution", cons,
            "Uniform α (FCC) grains. Under equilibrium cooling the composition is the same everywhere; with fast cooling the grains show coring (Ni-rich centres, Cu-rich edges).",
            "Strengthened by solid-solution hardening; excellent corrosion resistance (cupronickel, constantan).")
    return Microstructure("Solid + liquid (mushy zone)", cons,
                          "Ni-rich α crystals growing in the remaining Cu-rich liquid. Both phases change composition as T falls (tie-line moves along the boundaries).")


_ANALYZERS = {"fe_c": _iron_carbon, "pb_sn": _eutectic_binary, "cu_ni": _isomorphous}


def analyze(diagram: PhaseDiagram, eq: Equilibrium) -> Microstructure:
    """Microstructure of the alloy at the evaluated (X, T) for slow cooling."""
    return _ANALYZERS[diagram.key](diagram, eq)
