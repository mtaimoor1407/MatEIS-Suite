import math
from pathlib import Path

import numpy as np
import pytest

from core.corrosion.emf import ENVIRONMENT_FACTORS, Electrode, EMFDatabase, assess_couple, delta_matrix, risk_level
from core.corrosion.materials import MATERIALS, equivalent_weight, get_material
from core.corrosion.protection import ANODES, ENVIRONMENTS, get_environment, recommend, recommended_anode, size_anodes
from core.corrosion.rates import (
    butler_volmer_data,
    electrochemical_rate,
    rate_rating,
    service_life,
    stern_geary,
    tafel_extrapolation,
    weight_loss_rate,
)
from core.exceptions import DuplicateMaterialError, MaterialNotFoundError, ValidationError
from core.reporting.corrosion_report import corrosion_pdf

SEED = Path(__file__).resolve().parent.parent / "data" / "emf_series.json"


@pytest.fixture
def emf(tmp_path):
    db = EMFDatabase(tmp_path / "emf.db")
    db.seed_from_json(SEED)
    return db


@pytest.mark.parametrize("key,ew", [("carbon_steel", 27.92), ("al_pure", 8.99), ("copper", 31.77), ("zinc", 32.69), ("ss304", 25.12)])
def test_equivalent_weights_match_astm_g102(key, ew):
    assert get_material(key).equivalent_weight == pytest.approx(ew, rel=0.01)


def test_equivalent_weight_normalises_fractions():
    assert equivalent_weight({"Fe": 50}) == pytest.approx(equivalent_weight({"Fe": 1}))


@pytest.mark.parametrize("comp", [{}, {"Xx": 1}, {"Fe": -1}, {"Fe": 0}])
def test_equivalent_weight_rejects_bad_composition(comp):
    with pytest.raises(ValidationError):
        equivalent_weight(comp)


def test_unknown_material_rejected():
    with pytest.raises(ValidationError):
        get_material("unobtainium")


def test_weight_loss_known_value():
    r = weight_loss_rate(10.0, 9.98, 20, 720, 7.85)
    assert r.mm_per_year == pytest.approx(8.76e4 * 0.02 / (20 * 720 * 7.85))
    assert r.mpy == pytest.approx(r.mm_per_year * 39.3701)
    assert r.um_per_year == pytest.approx(r.mm_per_year * 1000)


def test_weight_loss_callister_equation_agrees():
    w_mg, rho, a_in2, t = 50.0, 7.85, 3.0, 1000.0
    r = weight_loss_rate(5.0, 5.0 - w_mg / 1000, a_in2 * 6.4516, t, rho)
    assert r.mpy == pytest.approx(534 * w_mg / (rho * a_in2 * t), rel=0.01)


@pytest.mark.parametrize("args", [(10, 10, 20, 100, 7.8), (10, 11, 20, 100, 7.8), (0, 0, 20, 100, 7.8), (10, 9, 0, 100, 7.8),
                                  (10, 9, 20, 0, 7.8), (10, 9, 20, 100, -1), (10, 9, math.nan, 100, 7.8), (10, 9, 20, math.inf, 7.8),
                                  ("a", 9, 20, 100, 7.8), (True, 9, 20, 100, 7.8)])
def test_weight_loss_rejects_invalid_inputs(args):
    with pytest.raises(ValidationError):
        weight_loss_rate(*args)


def test_icorr_conversion_matches_astm_g102():
    assert electrochemical_rate(1, 27.92, 7.85).mm_per_year == pytest.approx(0.01163, rel=0.01)


def test_icorr_is_linear_in_current():
    a = electrochemical_rate(2, 27.92, 7.85).mm_per_year
    assert electrochemical_rate(4, 27.92, 7.85).mm_per_year == pytest.approx(2 * a)


def test_faraday_mass_loss_consistent_with_rate():
    r = electrochemical_rate(10, 27.92, 7.85)
    assert r.mass_loss_g_m2_year / 7.85 / 1e3 == pytest.approx(r.mm_per_year, rel=0.01)


@pytest.mark.parametrize("bad", [0, -1, math.nan, "x", None])
def test_icorr_rejects_bad_values(bad):
    with pytest.raises(ValidationError):
        electrochemical_rate(bad, 27.92, 7.85)


def test_tafel_recovers_known_parameters():
    e, i = butler_volmer_data(1e-5, -0.45, 0.08, 0.12, eta_max=0.40, n=161)
    fit = tafel_extrapolation(e, i, -0.45, (0.10, 0.35))
    assert fit.i_corr == pytest.approx(1e-5, rel=0.03)
    assert fit.beta_a == pytest.approx(0.08, rel=0.03) and fit.beta_c == pytest.approx(0.12, rel=0.03)
    assert fit.e_corr_fit == pytest.approx(-0.45, abs=0.005)
    assert fit.r2_anodic > 0.99 and fit.r2_cathodic > 0.99


def test_tafel_tolerates_noise():
    e, i = butler_volmer_data(5e-6, -0.3, 0.06, 0.10, eta_max=0.4, n=161, noise=0.03)
    assert tafel_extrapolation(e, i, -0.3, (0.1, 0.35)).i_corr == pytest.approx(5e-6, rel=0.15)


def test_tafel_accepts_signed_or_absolute_current():
    e, i = butler_volmer_data(1e-5, -0.45, 0.08, 0.12, n=161)
    assert tafel_extrapolation(e, i, -0.45).i_corr == pytest.approx(tafel_extrapolation(e, np.abs(i), -0.45).i_corr)


@pytest.mark.parametrize("window", [(0.25, 0.05), (-0.1, 0.2), (0.1, 0.1)])
def test_tafel_rejects_bad_window(window):
    e, i = butler_volmer_data(1e-5, -0.45, 0.08, 0.12)
    with pytest.raises(ValidationError):
        tafel_extrapolation(e, i, -0.45, window)


def test_tafel_rejects_too_few_points_and_mismatched_lists():
    with pytest.raises(ValidationError):
        tafel_extrapolation([-0.5, -0.4], [1e-6, 1e-6], -0.45)
    with pytest.raises(ValidationError):
        tafel_extrapolation([-0.5, -0.4, -0.3], [1e-6, 1e-6], -0.45)
    with pytest.raises(ValidationError):
        tafel_extrapolation([math.nan] * 8, [1e-6] * 8, -0.45)


def test_tafel_rejects_wrong_slopes():
    e = np.array([0.06, 0.1, 0.15, 0.2, -0.06, -0.1, -0.15, -0.2]) - 0.4
    i = np.array([1e-4, 1e-5, 1e-6, 1e-7, 1e-4, 1e-5, 1e-6, 1e-7])
    with pytest.raises(ValidationError):
        tafel_extrapolation(e, i, -0.4)


def test_stern_geary():
    b, icorr = stern_geary(5000, 0.12, 0.12)
    assert b == pytest.approx(0.12 * 0.12 / (2.303 * 0.24)) and icorr == pytest.approx(b / 5000)
    with pytest.raises(ValidationError):
        stern_geary(0, 0.1, 0.1)


@pytest.mark.parametrize("rate,name", [(0.0, "Outstanding"), (0.019, "Outstanding"), (0.02, "Excellent"), (0.1, "Good"), (0.5, "Fair"),
                                       (1.0, "Poor"), (5.0, "Unacceptable"), (1e6, "Unacceptable")])
def test_rating_boundaries(rate, name):
    assert rate_rating(rate)[0] == name


def test_service_life():
    assert service_life(10, 0.5) == 20
    assert service_life(10, 0.5, 0.5) == 10
    for args in [(0, 1), (1, 0), (1, 1, 0), (1, 1, 1.5)]:
        with pytest.raises(ValidationError):
            service_life(*args)


def test_seed_has_both_series(emf):
    assert emf.count("standard") >= 15 and emf.count("seawater") >= 15


def test_series_are_sorted_active_to_noble(emf):
    for s in ("standard", "seawater"):
        vals = [e.potential_v for e in emf.list(s)]
        assert vals == sorted(vals)


def test_textbook_potentials(emf):
    for name, v in [("Zinc", -0.763), ("Iron", -0.440), ("Copper", 0.340), ("Aluminum", -1.662), ("Gold", 1.420)]:
        assert emf.find(name, "standard").potential_v == v


def test_crud_and_duplicates(emf):
    e = emf.add(Electrode("Beryllium", -1.847, "standard", custom=True))
    assert emf.get(e.id).custom
    with pytest.raises(DuplicateMaterialError):
        emf.add(Electrode("Beryllium", -1.0, "standard"))
    assert emf.update(e.id, Electrode("Beryllium", -1.85, "standard")).potential_v == -1.85
    emf.delete(e.id)
    with pytest.raises(MaterialNotFoundError):
        emf.get(e.id)
    with pytest.raises(MaterialNotFoundError):
        emf.find("Nope", "standard")


@pytest.mark.parametrize("kw", [dict(name="", potential_v=0), dict(name="X", potential_v=5), dict(name="X", potential_v=-9),
                                dict(name="X", potential_v=math.nan), dict(name="X", potential_v="a"), dict(name="X", potential_v=True),
                                dict(name="X", potential_v=0, series="bogus")])
def test_electrode_validation(kw):
    with pytest.raises(ValidationError):
        Electrode(**kw)


def test_anode_is_the_less_noble_metal(emf):
    a = assess_couple(emf.find("Copper", "standard"), emf.find("Zinc", "standard"))
    assert a.anode.name == "Zinc" and a.cathode.name == "Copper" and a.delta_e == pytest.approx(1.103)


def test_same_metal_or_mixed_series_rejected(emf):
    z = emf.find("Zinc", "standard")
    with pytest.raises(ValidationError):
        assess_couple(z, z)
    with pytest.raises(ValidationError):
        assess_couple(z, emf.find("Zinc", "seawater"))


def test_risk_grows_with_potential_difference(emf):
    steel = emf.find("Carbon / mild steel", "seawater")
    scores = [assess_couple(steel, emf.find(n, "seawater"), 1, "Seawater immersion").score
              for n in ("Cast iron", "Copper", "Stainless steel 304 (passive)", "Graphite")]
    assert scores == sorted(scores)


def test_risk_grows_with_cathode_area(emf):
    a, b = emf.find("Carbon / mild steel", "seawater"), emf.find("Copper", "seawater")
    s = [assess_couple(a, b, r, "Seawater immersion").score for r in (0.1, 1, 10, 100)]
    assert s == sorted(s) and s[0] < s[-1]


def test_dry_air_is_safer_than_seawater(emf):
    a, b = emf.find("Aluminum (1100 / 5052 / 6061)", "seawater"), emf.find("Copper", "seawater")
    assert assess_couple(a, b, 1, "Indoor dry atmosphere").score < assess_couple(a, b, 1, "Seawater immersion").score


def test_known_cases(emf):
    def sw(n):
        return emf.find(n, "seawater")
    assert assess_couple(sw("Carbon / mild steel"), sw("Stainless steel 304 (passive)"), 10).level == "Severe"
    assert assess_couple(sw("Carbon / mild steel"), sw("Cast iron"), 1, "Rural atmosphere").level == "Negligible"


@pytest.mark.parametrize("ratio", [0, -1, math.nan, math.inf, "x", True])
def test_invalid_area_ratio(emf, ratio):
    with pytest.raises(ValidationError):
        assess_couple(emf.find("Zinc", "standard"), emf.find("Copper", "standard"), ratio)


def test_unknown_environment(emf):
    with pytest.raises(ValidationError):
        assess_couple(emf.find("Zinc", "standard"), emf.find("Copper", "standard"), 1, "Mars")


def test_mitigations_scale_with_risk(emf):
    low = assess_couple(emf.find("Cast iron", "seawater"), emf.find("Carbon / mild steel", "seawater"), 1, "Rural atmosphere")
    high = assess_couple(emf.find("Zinc", "seawater"), emf.find("Copper", "seawater"), 10)
    assert len(high.mitigations) > len(low.mitigations)


def test_delta_matrix_is_symmetric_with_zero_diagonal(emf):
    es = [emf.find(n, "standard") for n in ("Zinc", "Iron", "Copper")]
    m = delta_matrix(es)
    assert all(m[i][i] == 0 for i in range(3)) and m[0][2] == m[2][0]
    with pytest.raises(ValidationError):
        delta_matrix([emf.find("Zinc", "standard"), emf.find("Zinc", "seawater")])


def test_risk_level_thresholds():
    assert [risk_level(s)[0] for s in (0, 1, 2, 3, 5)] == ["Negligible", "Low", "Moderate", "High", "Severe"]
    assert set(ENVIRONMENT_FACTORS) == set(ENVIRONMENTS)


def test_anode_mass_hand_calculation():
    d = size_anodes(ANODES["zinc"], 10, 100, 10)
    assert d.current_a == pytest.approx(1.0) and d.mass_kg == pytest.approx(1.0 * 10 * 8766 / (780 * 0.85), rel=1e-6)


def test_anode_scaling_laws():
    base = size_anodes(ANODES["aluminum"], 10, 100, 10).mass_kg
    assert size_anodes(ANODES["aluminum"], 20, 100, 10).mass_kg == pytest.approx(2 * base)
    assert size_anodes(ANODES["aluminum"], 10, 100, 10, breakdown_factor=0.1).mass_kg == pytest.approx(0.1 * base)
    assert size_anodes(ANODES["magnesium"], 10, 100, 10).mass_kg > base


@pytest.mark.parametrize("kw", [dict(area_m2=0), dict(area_m2=-1), dict(current_density_ma_m2=0), dict(life_years=0),
                                dict(breakdown_factor=0), dict(breakdown_factor=1.5), dict(utilization=0.1), dict(utilization=1.5),
                                dict(area_m2=math.nan), dict(area_m2="x")])
def test_anode_rejects_bad_inputs(kw):
    args = dict(area_m2=10, current_density_ma_m2=100, life_years=10)
    args.update(kw)
    with pytest.raises(ValidationError):
        size_anodes(ANODES["zinc"], **args)


def test_anode_choice_follows_environment():
    steel = get_material("carbon_steel")
    assert recommended_anode(steel, get_environment("Seawater immersion")).key == "aluminum"
    assert recommended_anode(steel, get_environment("Buried in soil")).key == "magnesium"
    assert recommended_anode(steel, get_environment("Indoor dry atmosphere")) is None
    assert recommended_anode(get_material("titanium"), get_environment("Seawater immersion")) is None


def test_steel_in_seawater_gets_coating_and_cathodic_protection():
    cats = {r.category for r in recommend(get_material("carbon_steel"), get_environment("Seawater immersion"))}
    assert {"Coating", "Cathodic protection"} <= cats


def test_steel_in_marine_air_mentions_zinc_and_life_estimate():
    recs = recommend(get_material("carbon_steel"), get_environment("Marine atmosphere (coastal)"))
    galv = [r for r in recs if "galvaniz" in r.title.lower()][0]
    assert any("years" in d for d in galv.details)


def test_recommendations_are_sorted_and_corrosion_allowance_uses_rate():
    recs = recommend(get_material("carbon_steel"), get_environment("Rural atmosphere"), 20, 0.1)
    assert [r.priority for r in recs] == sorted(r.priority for r in recs)
    assert any("2.00 mm" in r.title for r in recs)


def test_galvanic_partner_adds_design_action():
    recs = recommend(get_material("carbon_steel"), get_environment("Seawater immersion"), 20, None, "Copper", "Severe")
    assert any("Break the galvanic couple" in r.title for r in recs)
    recs = recommend(get_material("carbon_steel"), get_environment("Seawater immersion"), 20, None, "Cast iron", "Low")
    assert not any("Break the galvanic couple" in r.title for r in recs)


@pytest.mark.parametrize("key", list(MATERIALS))
@pytest.mark.parametrize("env", list(ENVIRONMENTS))
def test_every_material_environment_combination_gives_advice(key, env):
    recs = recommend(get_material(key), get_environment(env), 25)
    assert len(recs) >= 2 and all(r.why for r in recs)


def test_invalid_service_life_and_environment():
    with pytest.raises(ValidationError):
        recommend(get_material("carbon_steel"), get_environment("Rural atmosphere"), 0)
    with pytest.raises(ValidationError):
        get_environment("Mars")


def test_corrosion_pdf_with_and_without_sections(emf):
    assert corrosion_pdf("Carbon steel", "Rural atmosphere", 20).startswith(b"%PDF")
    rate = weight_loss_rate(10, 9.9, 20, 500, 7.85)
    g = assess_couple(emf.find("Zinc", "standard"), emf.find("Copper", "standard"))
    recs = recommend(get_material("carbon_steel"), get_environment("Seawater immersion"))
    pdf = corrosion_pdf("Carbon steel", "Seawater immersion", 20, rate, None, g, emf.list("standard"), recs, size_anodes(ANODES["zinc"], 10, 100, 10))
    assert pdf.startswith(b"%PDF") and len(pdf) > 10_000
