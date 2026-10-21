"""The three built-in binary diagrams: Cu–Ni, Pb–Sn and Fe–Fe₃C.

Boundary curves are piece-wise linear approximations digitised from standard
textbook diagrams (Callister & Rethwisch, *Materials Science and Engineering*,
Figs. 9.3a, 9.8 and 9.24), tuned so that the worked textbook examples reproduce:

    Cu–Ni, 35 wt% Ni at 1250 °C  ->  C_L = 31.5, C_α = 42.5 wt% Ni, W_α = 0.32
    Pb–Sn, 40 wt% Sn at 150 °C   ->  C_α = 11,   C_β = 99 wt% Sn,  W_α = 0.67
    Fe–C,  0.35 wt% C below 727  ->  W_proeutectoid α = 0.55, W_pearlite = 0.45

Accuracy is about ±10 °C and ±1 wt%. Check against your own textbook figure
(see docs/DATA_VERIFICATION.md) before relying on a number.
"""
from __future__ import annotations

import math

from core.exceptions import ValidationError
from core.phase.diagram import Invariant, PhaseDiagram, Region

CALLISTER = "Callister & Rethwisch, Materials Science and Engineering"


def _rev(points):
    return list(reversed(points))


def cu_ni() -> PhaseDiagram:
    liq = [(0, 1085), (10, 1135), (20, 1181), (31.5, 1250), (40, 1282), (50, 1316),
           (60, 1347), (70, 1376), (80, 1404), (90, 1431), (100, 1455)]
    sol = [(0, 1085), (10, 1108), (20, 1145), (30, 1190), (42.5, 1250), (50, 1280),
           (60, 1315), (70, 1348), (80, 1382), (90, 1420), (100, 1455)]
    regions = [
        Region("L", ("L",), tuple([(0, 1600), (100, 1600)] + _rev(liq)), "#E4572E", (35, 1470)),
        Region("L + α", ("L", "α"), tuple(liq + _rev(sol)[1:-1]), "#F2A65A", (66, 1335)),
        Region("α", ("α",), tuple(sol + [(100, 1000), (0, 1000)]), "#4F86C6", (68, 1150)),
    ]
    return PhaseDiagram(
        "cu_ni", "Cu–Ni (isomorphous)", "Cu", "Ni", "wt% Ni", (0, 100), (1000, 1600), regions, [], [],
        f"{CALLISTER}, Fig. 9.3a (digitised)", "Complete solid solubility: one solid phase (α, FCC) at all compositions.",
        melting_a=1085, melting_b=1455,
        phase_names={"L": "Liquid", "α": "α solid solution (Cu–Ni, FCC)"})


def pb_sn() -> PhaseDiagram:
    liq_l = [(0, 327.5), (10, 302), (20, 279), (30, 258), (40, 236), (50, 214), (61.9, 183)]
    liq_r = [(61.9, 183), (70, 193), (80, 203), (90, 216), (100, 231.9)]
    sol_a = [(0, 327.5), (5, 298), (10, 265), (15, 225), (18.3, 183)]
    sol_b = [(97.8, 183), (98.5, 200), (99.3, 217), (100, 231.9)]
    solv_a = [(18.3, 183), (11, 150), (6, 100), (3, 50), (1.8, 20), (1.5, 0)]
    solv_b = [(97.8, 183), (99.0, 150), (99.5, 100), (99.8, 50), (99.9, 20), (99.95, 0)]
    regions = [
        Region("L", ("L",), tuple(liq_l + liq_r[1:] + [(100, 350), (0, 350)]), "#E4572E", (50, 300)),
        Region("α", ("α",), tuple([(0, 0), (0, 327.5)] + sol_a[1:] + solv_a[1:]), "#4F86C6", (4, 150)),
        Region("L + α", ("α", "L"), tuple(liq_l + [(18.3, 183)] + _rev(sol_a)[1:-1]), "#F2A65A", (33, 215)),
        Region("L + β", ("L", "β"), tuple(liq_r + _rev(sol_b)[1:]), "#F6C177", (86, 190)),
        Region("β", ("β",), tuple([(100, 0), (100, 231.9)] + _rev(sol_b)[1:] + solv_b[1:]), "#8BC6A1", (99.4, 120)),
        Region("α + β", ("α", "β"), tuple(_rev(solv_a) + [(97.8, 183)] + solv_b[1:]), "#9D8DC9", (55, 90)),
    ]
    inv = [Invariant("Eutectic", "L → α + β", 183.0, 18.3, 61.9, 97.8)]
    return PhaseDiagram(
        "pb_sn", "Pb–Sn (simple eutectic)", "Pb", "Sn", "wt% Sn", (0, 100), (0, 350), regions, inv, [],
        f"{CALLISTER}, Fig. 9.8 (digitised)", "Eutectic at 183 °C and 61.9 wt% Sn (solder composition).",
        melting_a=327.5, melting_b=231.9,
        phase_names={"L": "Liquid", "α": "α (Pb-rich solid solution)", "β": "β (Sn-rich solid solution)"})


def fe_fe3c() -> PhaseDiagram:
    a3 = [(0.0, 912.0)] + [(c, 912.0 - 212.2 * math.sqrt(c)) for c in (0.02, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6)] + [(0.76, 727.0)]
    alpha_b = [(0, 912), (0.004, 860), (0.01, 800), (0.017, 760), (0.022, 727)]
    acm = [(0.76, 727), (1.0, 798), (1.4, 918), (1.8, 1035), (2.14, 1147)]
    solvus = [(0.022, 727), (0.015, 600), (0.008, 400), (0.005, 200), (0.004, 0)]
    F = "Fe₃C"
    regions = [
        Region("L", ("L",), ((0, 1600), (6.70, 1600), (6.70, 1227), (4.30, 1147), (0.53, 1493), (0, 1538)), "#E4572E", (3.2, 1400)),
        Region("L + δ", ("δ", "L"), ((0, 1538), (0.53, 1493), (0.09, 1493)), "#EF8354", (0.3, 1515)),
        Region("δ", ("δ",), ((0, 1394), (0, 1538), (0.09, 1493)), "#7FB7BE", (0.03, 1480)),
        Region("δ + γ", ("δ", "γ"), ((0, 1394), (0.09, 1493), (0.17, 1493)), "#6A9FB5", (0.1, 1450)),
        Region("L + γ", ("γ", "L"), ((0.17, 1493), (0.53, 1493), (4.30, 1147), (2.14, 1147)), "#F2A65A", (2.2, 1300)),
        Region(f"L + {F}", ("L", F), ((4.30, 1147), (6.70, 1227), (6.70, 1147)), "#F6C177", (5.9, 1185)),
        Region("γ", ("γ",), tuple([(0, 912), (0, 1394), (0.17, 1493), (2.14, 1147)] + _rev(acm)[1:] + _rev(a3)[1:-1]), "#4F86C6", (0.9, 1050)),
        Region("α + γ", ("α", "γ"), tuple(a3 + [(0.022, 727)] + _rev(alpha_b)[1:-1]), "#6C8EBF", (0.3, 800)),
        Region("α", ("α",), tuple([(0, 0), (0, 912)] + alpha_b[1:] + solvus[1:]), "#8BC6A1", (0.011, 400)),
        Region(f"α + {F}", ("α", F), tuple(_rev(solvus) + [(6.70, 727), (6.70, 0)]), "#9D8DC9", (3.5, 380)),
        Region(f"γ + {F}", ("γ", F), tuple(acm + [(6.70, 1147), (6.70, 727)]), "#B68DBF", (4.2, 930)),
    ]
    inv = [
        Invariant("Peritectic", "L + δ → γ", 1493.0, 0.09, 0.17, 0.53),
        Invariant("Eutectic", f"L → γ + {F}", 1147.0, 2.14, 4.30, 6.70),
        Invariant("Eutectoid", f"γ → α + {F}", 727.0, 0.022, 0.76, 6.70),
    ]
    return PhaseDiagram(
        "fe_c", f"Fe–{F} (iron–carbon)", "Fe", "C", "wt% C", (0, 6.70), (0, 1600), regions, inv, [],
        f"{CALLISTER}, Fig. 9.24 (digitised)",
        "Steels lie below 2.14 wt% C, cast irons above. Eutectoid at 0.76 wt% C and 727 °C; eutectic at 4.30 wt% C and 1147 °C.",
        melting_a=1538, melting_b=None,
        phase_names={"L": "Liquid", "α": "Ferrite (α, BCC)", "γ": "Austenite (γ, FCC)", "δ": "δ-ferrite (BCC)", F: "Cementite (Fe₃C)"})


_FACTORIES = {"fe_c": fe_fe3c, "cu_ni": cu_ni, "pb_sn": pb_sn}
_CACHE: dict[str, PhaseDiagram] = {}


def available_diagrams() -> dict[str, str]:
    """key -> title, in display order."""
    return {k: get_diagram(k).title for k in _FACTORIES}


def get_diagram(key: str) -> PhaseDiagram:
    if key not in _FACTORIES:
        raise ValidationError(f"Unknown phase diagram '{key}'.")
    if key not in _CACHE:
        _CACHE[key] = _FACTORIES[key]()
    return _CACHE[key]
