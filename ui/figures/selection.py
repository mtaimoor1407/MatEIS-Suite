"""Plotly charts for the materials-selection page (interactive Ashby chart)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from core.selection.indices import PerformanceIndex, guide_line
from core.selection.properties import CLASS_COLORS, EXCLUDED_COLOR, MATERIAL_CLASSES, WINNER_COLOR, axis_label


def convex_hull(points: np.ndarray) -> np.ndarray:
    """Andrew's monotone chain. ``points`` is (n, 2); returns hull vertices in order."""
    pts = sorted({(float(x), float(y)) for x, y in points})
    if len(pts) <= 2:
        return np.array(pts)

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return np.array(lower[:-1] + upper[:-1])


def _hover(row: pd.Series) -> str:
    return (f"<b>{row['name']}</b><br>{row['material_class']}<br>"
            f"ρ = {row['density']:.2f} Mg/m³<br>E = {row['modulus']:.3g} GPa<br>"
            f"σ ({row['strength_basis']}) = {row['strength']:.4g} MPa<br>"
            f"Cost = {row['cost']:.3g} USD/kg")


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def ashby_figure(all_df: pd.DataFrame, ranked: pd.DataFrame, index: PerformanceIndex,
                 x_key: str, y_key: str, show_hulls: bool = True, dark: bool = True) -> go.Figure:
    """Log-log Ashby chart with class envelopes, excluded points, guide line and winner."""
    soft = "#9FB0C7" if dark else "#4B5B6E"
    fig = go.Figure()
    passing = set(ranked["name"]) if not ranked.empty else set()

    if show_hulls:
        for cls in MATERIAL_CLASSES:
            sub = all_df[(all_df["material_class"] == cls) & all_df["name"].isin(passing)]
            if len(sub) >= 3:
                hull = convex_hull(np.log10(sub[[x_key, y_key]].to_numpy(dtype=float)))
                if len(hull) >= 3:
                    hx, hy = 10 ** hull[:, 0], 10 ** hull[:, 1]
                    fig.add_trace(go.Scatter(
                        x=np.append(hx, hx[0]), y=np.append(hy, hy[0]), mode="lines", fill="toself",
                        line=dict(color=_rgba(CLASS_COLORS[cls], 0.5), width=1),
                        fillcolor=_rgba(CLASS_COLORS[cls], 0.10), hoverinfo="skip", showlegend=False))

    excluded = all_df[~all_df["name"].isin(passing)]
    if not excluded.empty:
        fig.add_trace(go.Scatter(
            x=excluded[x_key], y=excluded[y_key], mode="markers", name="Excluded by constraints",
            marker=dict(size=8, color=EXCLUDED_COLOR, line=dict(width=0)),
            hovertext=[_hover(r) for _, r in excluded.iterrows()], hoverinfo="text"))

    for cls in MATERIAL_CLASSES:
        sub = ranked[ranked["material_class"] == cls] if not ranked.empty else ranked
        if len(sub):
            fig.add_trace(go.Scatter(
                x=sub[x_key], y=sub[y_key], mode="markers", name=cls,
                marker=dict(size=11, color=CLASS_COLORS[cls], line=dict(color="white", width=1)),
                hovertext=[_hover(r) + f"<br>M = {r['index_value']:.3g} (rank {int(r['rank'])})"
                           for _, r in sub.iterrows()], hoverinfo="text"))

    if not ranked.empty:
        best = ranked.iloc[0]
        if (x_key, y_key) == index.axes:
            gx, gy = guide_line(index, best[x_key], best[y_key],
                                all_df[x_key].min() / 1.6, all_df[x_key].max() * 1.6)
            fig.add_trace(go.Scatter(
                x=gx, y=gy, mode="lines", name=f"Guide line M = {best['index_value']:.3g}",
                line=dict(color=WINNER_COLOR, width=1.5, dash="dash"), hoverinfo="skip"))
        fig.add_trace(go.Scatter(
            x=[best[x_key]], y=[best[y_key]], mode="markers+text", name=f"Best: {best['name']}",
            text=[best["name"]], textposition="top center", textfont=dict(size=11, color=WINNER_COLOR),
            marker=dict(size=20, symbol="star", color=WINNER_COLOR, line=dict(color="white", width=1)),
            hovertext=[_hover(best) + f"<br>M = {best['index_value']:.3g}"], hoverinfo="text"))

    fig.update_xaxes(type="log", title=axis_label(x_key), showgrid=True, gridcolor="rgba(150,165,185,0.18)", color=soft, zeroline=False,
                     range=[np.log10(all_df[x_key].min() / 1.6), np.log10(all_df[x_key].max() * 1.6)])
    fig.update_yaxes(type="log", title=axis_label(y_key), showgrid=True, gridcolor="rgba(150,165,185,0.18)", color=soft, zeroline=False,
                     range=[np.log10(all_df[y_key].min() / 1.6), np.log10(all_df[y_key].max() * 1.6)])
    fig.update_layout(height=560, margin=dict(l=10, r=10, t=30, b=10), hovermode="closest",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(color=soft)),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color=soft))
    return fig
