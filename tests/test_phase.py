import math
import random

import pytest

from core.exceptions import ValidationError
from core.phase.diagram import horizontal_crossings, point_in_polygon, polygon_area, polygon_centroid
from core.phase.diagrams import available_diagrams, get_diagram
from core.phase.microstructure import analyze
from core.phase.schematic import render_png
from core.reporting.phase_report import phase_pdf

KEYS = list(available_diagrams())


def test_polygon_area_and_centroid():
    square = ((0, 0), (4, 0), (4, 2), (0, 2))
    assert polygon_area(square) == 8
    assert polygon_centroid(square) == pytest.approx((2, 1))


def test_point_in_polygon_inside_outside_edge_vertex():
    sq = ((0, 0), (4, 0), (4, 4), (0, 4))
    assert point_in_polygon(2, 2, sq) and not point_in_polygon(5, 2, sq)
    assert point_in_polygon(4, 2, sq) and point_in_polygon(0, 0, sq)


def test_horizontal_crossings_of_triangle():
    tri = ((0, 0), (4, 0), (2, 4))
    assert sorted(horizontal_crossings(tri, 2)) == pytest.approx([1, 3])


@pytest.mark.parametrize("key", KEYS)
def test_regions_tile_the_diagram_exactly(key):
    d = get_diagram(key)
    assert d.total_area() == pytest.approx(d.bounding_area(), rel=1e-9)


@pytest.mark.parametrize("key", KEYS)
def test_every_random_point_is_in_exactly_one_region(key):
    d = get_diagram(key)
    rng = random.Random(5)
    for _ in range(1500):
        x, t = rng.uniform(*d.x_range), rng.uniform(*d.t_range)
        n = sum(point_in_polygon(x, t, r.polygon) for r in d.regions)
        assert n >= 1
        if n > 1:
            raise AssertionError(f"overlap at {x}, {t}")


@pytest.mark.parametrize("key", KEYS)
def test_lever_rule_fractions_sum_to_one_and_balance_mass(key):
    d = get_diagram(key)
    rng = random.Random(9)
    for _ in range(400):
        x, t = rng.uniform(*d.x_range), rng.uniform(*d.t_range)
        eq = d.equilibrium(x, t)
        assert sum(p.fraction for p in eq.phases) == pytest.approx(1.0)
        assert all(0 <= p.fraction <= 1 for p in eq.phases)
        assert sum(p.fraction * p.composition for p in eq.phases) == pytest.approx(x, abs=1e-6)


def test_cu_ni_callister_example():
    eq = get_diagram("cu_ni").equilibrium(35, 1250)
    assert eq.region.name == "L + α"
    liquid, alpha = eq.phases
    assert (liquid.composition, alpha.composition) == pytest.approx((31.5, 42.5))
    assert alpha.fraction == pytest.approx(0.318, abs=0.005) and liquid.fraction == pytest.approx(0.682, abs=0.005)


def test_pb_sn_callister_example():
    eq = get_diagram("pb_sn").equilibrium(40, 150)
    a, b = eq.phases
    assert (a.composition, b.composition) == pytest.approx((11, 99))
    assert a.fraction == pytest.approx(0.67, abs=0.005) and b.fraction == pytest.approx(0.33, abs=0.005)


def test_iron_carbon_lever_below_eutectoid():
    eq = get_diagram("fe_c").equilibrium(0.35, 600)
    assert eq.region.name == "α + Fe₃C"
    alpha = eq.phases[0]
    assert alpha.fraction == pytest.approx((6.70 - 0.35) / (6.70 - alpha.composition))


@pytest.mark.parametrize("x,t,name", [(0.4, 1550, "L"), (0.4, 1500, "L + δ"), (0.4, 900, "γ"), (0.4, 760, "α + γ"), (0.4, 600, "α + Fe₃C"),
                                      (1.2, 800, "γ + Fe₃C"), (3.0, 1200, "L + γ"), (6.3, 1200, "L + Fe₃C"), (0.005, 400, "α"), (3.0, 1300, "L")])
def test_iron_carbon_regions(x, t, name):
    assert get_diagram("fe_c").locate(x, t).name == name


def test_single_phase_is_one_hundred_percent():
    eq = get_diagram("cu_ni").equilibrium(50, 1100)
    assert eq.is_single_phase and eq.phases[0].fraction == 1.0 and eq.tie_line is None


@pytest.mark.parametrize("key,x,t", [("pb_sn", 40, 183), ("fe_c", 0.4, 727), ("fe_c", 3.0, 1147), ("fe_c", 0.12, 1493)])
def test_point_on_invariant_line_is_handled_and_explained(key, x, t):
    eq = get_diagram(key).equilibrium(x, t)
    assert eq.effective_temperature == pytest.approx(t - 0.01) and eq.notes
    assert sum(p.fraction for p in eq.phases) == pytest.approx(1.0)


def test_outside_invariant_span_is_not_nudged():
    assert get_diagram("pb_sn").equilibrium(5, 183).effective_temperature is None


@pytest.mark.parametrize("key", KEYS)
def test_corners_and_edges_of_the_diagram_work(key):
    d = get_diagram(key)
    for x in d.x_range:
        for t in d.t_range:
            eq = d.equilibrium(x, t)
            assert sum(p.fraction for p in eq.phases) == pytest.approx(1.0)


@pytest.mark.parametrize("x,t", [(-0.1, 500), (100.01, 500), (50, -1), (50, 1e6), (math.nan, 500), (50, math.inf), ("a", 500), (True, 500), (None, 500)])
def test_out_of_range_input_rejected(x, t):
    with pytest.raises(ValidationError):
        get_diagram("pb_sn").equilibrium(x, t)


def test_unknown_diagram_rejected():
    with pytest.raises(ValidationError):
        get_diagram("al_si")


def test_pure_components_have_the_right_melting_points():
    cu = get_diagram("cu_ni")
    assert cu.locate(0, 1084).name == "α" and cu.locate(0, 1090).name == "L"
    fe = get_diagram("fe_c")
    assert fe.locate(0, 1500).name == "δ" and fe.locate(0, 1550).name == "L"


def micro(key, x, t):
    d = get_diagram(key)
    return analyze(d, d.equilibrium(x, t))


def test_hypoeutectoid_steel_matches_callister():
    m = micro("fe_c", 0.35, 25)
    assert m.classification == "Hypoeutectoid steel"
    by = {c.name: c.fraction for c in m.constituents}
    assert by["Proeutectoid ferrite"] == pytest.approx(0.55, abs=0.01) and by["Pearlite"] == pytest.approx(0.45, abs=0.01)


def test_hypereutectoid_steel_matches_callister():
    by = {c.name: c.fraction for c in micro("fe_c", 1.4, 25).constituents}
    assert by["Pearlite"] == pytest.approx(0.89, abs=0.01) and by["Proeutectoid cementite"] == pytest.approx(0.11, abs=0.01)


@pytest.mark.parametrize("x,label", [(0.01, "Commercially pure iron (ferrite)"), (0.76, "Eutectoid steel"), (4.30, "Eutectic white cast iron"),
                                     (3.0, "Hypoeutectic white cast iron"), (5.5, "Hypereutectic white cast iron")])
def test_iron_carbon_classification(x, label):
    assert micro("fe_c", x, 25).classification == label


@pytest.mark.parametrize("key,x,t", [("fe_c", 0.2, 25), ("fe_c", 3.5, 25), ("fe_c", 6.0, 25), ("pb_sn", 30, 25), ("pb_sn", 80, 25), ("cu_ni", 35, 1250)])
def test_constituent_fractions_sum_to_one(key, x, t):
    assert sum(c.fraction for c in micro(key, x, t).constituents) == pytest.approx(1.0)


def test_pb_sn_eutectic_and_hypoeutectic():
    assert [c.fraction for c in micro("pb_sn", 61.9, 25).constituents] == [1.0]
    by = {c.name: c.fraction for c in micro("pb_sn", 40, 25).constituents}
    assert by["Eutectic (α + β lamellae)"] == pytest.approx((40 - 18.3) / (61.9 - 18.3))


def test_above_eutectoid_shows_phases_only():
    m = micro("fe_c", 0.4, 760)
    assert m.classification == "Above the eutectoid temperature" and len(m.constituents) == 2


@pytest.mark.parametrize("key,x,t", [("fe_c", 0.35, 25), ("fe_c", 3.0, 25), ("pb_sn", 40, 25), ("cu_ni", 35, 1250), ("cu_ni", 35, 1500)])
def test_schematic_png_is_valid(key, x, t):
    assert render_png(micro(key, x, t), 200, 140)[:8] == b"\x89PNG\r\n\x1a\n"


def test_phase_pdf_is_valid():
    d = get_diagram("fe_c")
    eq = d.equilibrium(0.35, 700)
    assert phase_pdf(d, eq, analyze(d, eq)).startswith(b"%PDF")
