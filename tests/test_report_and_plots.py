import numpy as np
import pytest

from core.selection.filters import Constraints, apply_constraints
from core.selection.indices import INDICES, rank_materials
from core.selection.report import csv_bytes, pdf_report, static_ashby_figure
from ui.figures.selection import ashby_figure, convex_hull


@pytest.fixture
def ranked(df):
    return rank_materials(apply_constraints(df, Constraints(ranges={"strength": (200, None)})), INDICES["stiff_beam"])


def test_csv_has_header_and_rows(ranked):
    text = csv_bytes(ranked).decode("utf-8-sig").splitlines()
    assert text[0].startswith("rank,name") and len(text) == len(ranked) + 1


def test_pdf_is_valid(df, ranked):
    data = pdf_report(df, ranked, INDICES["stiff_beam"], Constraints(ranges={"strength": (200, None)}))
    assert data.startswith(b"%PDF") and len(data) > 5_000


def test_pdf_with_no_results_does_not_crash(df):
    empty = rank_materials(df.iloc[0:0], INDICES["stiff_beam"])
    assert pdf_report(df, empty, INDICES["stiff_beam"], Constraints()).startswith(b"%PDF")


def test_static_chart_is_loglog(df, ranked):
    ax = static_ashby_figure(df, ranked, INDICES["stiff_beam"]).axes[0]
    assert ax.get_xscale() == "log" and ax.get_yscale() == "log"


def test_convex_hull_ignores_interior_points():
    pts = np.array([[0, 0], [4, 0], [4, 4], [0, 4], [2, 2]], dtype=float)
    assert len(convex_hull(pts)) == 4


@pytest.mark.parametrize("n", [1, 2])
def test_convex_hull_small_inputs(n):
    assert len(convex_hull(np.array([[0, 0], [1, 1]], dtype=float)[:n])) == n


def test_collinear_points_hull_is_degenerate():
    assert len(convex_hull(np.array([[0, 0], [1, 1], [2, 2]], dtype=float))) <= 2


def test_plotly_chart_has_guide_line_and_winner(df, ranked):
    idx = INDICES["stiff_beam"]
    names = [t.name for t in ashby_figure(df, ranked, idx, *idx.axes).data if t.name]
    assert any(n.startswith("Guide line") for n in names) and any(n.startswith("Best:") for n in names)


def test_plotly_chart_custom_axes_has_no_guide_line(df, ranked):
    names = [t.name for t in ashby_figure(df, ranked, INDICES["stiff_beam"], "cost", "strength").data if t.name]
    assert not any(n.startswith("Guide line") for n in names)


def test_plotly_chart_with_no_results(df):
    empty = rank_materials(df.iloc[0:0], INDICES["stiff_beam"])
    assert len(ashby_figure(df, empty, INDICES["stiff_beam"], "density", "modulus").data) == 1
