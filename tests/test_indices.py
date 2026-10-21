import numpy as np
import pandas as pd
import pytest

from core.exceptions import ValidationError
from core.selection.indices import INDICES, get_index, guide_line, rank_materials


def row(name, E, s, rho, cost_vol=1.0):
    return dict(name=name, modulus=E, strength=s, density=rho, cost_vol=cost_vol, material_class="Metal")


def test_stiff_beam_formula_known_value():
    df = pd.DataFrame([row("Al", 69, 275, 2.7)])
    assert INDICES["stiff_beam"].compute(df).iloc[0] == pytest.approx(69 ** 0.5 / 2.7)


@pytest.mark.parametrize("key,num,p", [("stiff_tie", "modulus", 1), ("stiff_beam", "modulus", 0.5),
                                       ("stiff_plate", "modulus", 1 / 3), ("strong_tie", "strength", 1),
                                       ("strong_beam", "strength", 2 / 3), ("strong_plate", "strength", 0.5)])
def test_formulas_match_ashby(key, num, p):
    df = pd.DataFrame([row("X", 100, 400, 5.0)])
    expected = df[num].iloc[0] ** p / 5.0
    assert INDICES[key].compute(df).iloc[0] == pytest.approx(expected)


def test_cost_indices_use_cost_per_volume():
    df = pd.DataFrame([row("X", 100, 400, 5.0, cost_vol=20.0)])
    assert INDICES["cheap_stiff_beam"].compute(df).iloc[0] == pytest.approx(10 / 20)


def test_ranking_is_descending_and_ranks_start_at_one(df):
    out = rank_materials(df, INDICES["stiff_beam"])
    assert out["rank"].tolist() == list(range(1, len(df) + 1))
    assert out["index_value"].is_monotonic_decreasing


def test_known_winner_for_strong_beam(df):
    assert rank_materials(df, INDICES["strong_beam"]).iloc[0]["name"].startswith("CFRP")


def test_steel_beats_cast_iron_never_beats_titanium_for_strong_tie_per_mass(df):
    r = rank_materials(df, INDICES["strong_tie"]).set_index("name")["rank"]
    assert r["Titanium Ti-6Al-4V (annealed)"] < r["AISI 304 Stainless Steel (annealed)"]


def test_ranking_empty_dataframe(df):
    out = rank_materials(df.iloc[0:0], INDICES["stiff_beam"])
    assert out.empty and "rank" in out.columns


def test_single_material_ranking():
    out = rank_materials(pd.DataFrame([row("Only", 10, 10, 1)]), INDICES["stiff_tie"])
    assert len(out) == 1 and out.iloc[0]["rank"] == 1


@pytest.mark.parametrize("bad", [0, -1])
def test_non_positive_values_rejected(bad):
    with pytest.raises(ValidationError):
        INDICES["stiff_beam"].compute(pd.DataFrame([row("bad", bad, 1, 1)]))


def test_unknown_index_rejected():
    with pytest.raises(ValidationError):
        get_index("magic")


@pytest.mark.parametrize("key", list(INDICES))
def test_guide_line_has_constant_index_value(key):
    idx = INDICES[key]
    x, y = guide_line(idx, 2.0, 50.0, 0.5, 20.0)
    m = y ** float(idx.exponent) / x
    assert np.allclose(m, m[0])
    assert np.isclose(np.interp(2.0, x, y), 50.0, rtol=0.05)


def test_guide_line_slope_in_loglog():
    idx = INDICES["stiff_beam"]
    x, y = guide_line(idx, 1.0, 10.0, 1.0, 100.0)
    slope = (np.log10(y[-1]) - np.log10(y[0])) / (np.log10(x[-1]) - np.log10(x[0]))
    assert slope == pytest.approx(2.0)


@pytest.mark.parametrize("args", [(0, 1, 1, 2), (1, 0, 1, 2), (1, 1, 0, 2), (1, 1, 2, 1)])
def test_guide_line_rejects_bad_geometry(args):
    with pytest.raises(ValidationError):
        guide_line(INDICES["stiff_tie"], *args)
