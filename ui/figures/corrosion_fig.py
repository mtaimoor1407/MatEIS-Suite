"""Plotly figures for the corrosion page: Tafel (Evans) plot, potential ladder, compatibility matrix."""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from core.corrosion.emf import Electrode
from core.corrosion.rates import TafelFit

GRID = "rgba(150,165,185,0.18)"


def _soft(dark: bool) -> str:
    return "#9FB0C7" if dark else "#4B5B6E"


def _base(fig: go.Figure, dark: bool, height: int) -> go.Figure:
    soft = _soft(dark)
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      font=dict(color=soft), legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(color=soft)))
    fig.update_xaxes(gridcolor=GRID, color=soft, zeroline=False)
    fig.update_yaxes(gridcolor=GRID, color=soft, zeroline=False)
    return fig


def tafel_plotly(potentials, currents, e_corr: float, fit: TafelFit | None, window: tuple[float, float], dark: bool = True) -> go.Figure:
    e, i = np.asarray(potentials, float), np.abs(np.asarray(currents, float))
    eta = e - e_corr
    ok = (i > 0) & (np.abs(eta) >= 0.01)          # points at E_corr itself carry no Tafel information
    sel = ok & (np.abs(eta) >= window[0]) & (np.abs(eta) <= window[1])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=i[ok], y=e[ok], mode="markers", name="Polarization data", marker=dict(size=6, color="#8EA0B8")))
    fig.add_trace(go.Scatter(x=i[sel], y=e[sel], mode="markers", name="Points used for the fit", marker=dict(size=7, color="#5AA9FF")))
    if fit:
        lo = min(np.log10(i[ok].min()), np.log10(fit.i_corr)) - 0.3
        hi = np.log10(i[ok].max()) + 0.2
        lx = np.linspace(lo, hi, 40)
        fig.add_trace(go.Scatter(x=10 ** lx, y=fit.a_anodic + fit.beta_a * lx, mode="lines", name=f"Anodic Tafel line (βa = {fit.beta_a * 1000:.0f} mV/dec)", line=dict(color="#E4572E", width=2)))
        fig.add_trace(go.Scatter(x=10 ** lx, y=fit.a_cathodic - fit.beta_c * lx, mode="lines", name=f"Cathodic Tafel line (βc = {fit.beta_c * 1000:.0f} mV/dec)", line=dict(color="#2FBFA5", width=2)))
        fig.add_trace(go.Scatter(x=[fit.i_corr], y=[fit.e_corr_fit], mode="markers", name=f"i_corr = {fit.i_corr * 1e6:.3g} µA/cm²",
                                 marker=dict(size=18, symbol="star", color="#F0647A", line=dict(color="white", width=1))))
    fig.update_xaxes(type="log", title="|Current density| (A/cm²)")
    fig.update_yaxes(title="Potential (V)")
    _base(fig, dark, 460)
    if ok.any():
        lo_x = np.log10(i[ok].min()) - 0.3
        hi_x = np.log10(i[ok].max()) + 0.2
        if fit:
            lo_x = min(lo_x, np.log10(fit.i_corr) - 0.5)
        fig.update_xaxes(range=[lo_x, hi_x])
        fig.update_yaxes(range=[float(e[ok].min()) - 0.05, float(e[ok].max()) + 0.05])
    return fig


def ladder_plotly(entries: list[Electrode], highlight: tuple[str, str] | None, dark: bool = True) -> go.Figure:
    names = [e.name for e in entries]
    vals = [e.potential_v for e in entries]
    colors = ["#F0647A" if highlight and n in highlight else ("#2FBFA5" if v < 0 else "#8EA0B8") for n, v in zip(names, vals, strict=True)]
    fig = go.Figure(go.Bar(x=vals, y=names, orientation="h", marker=dict(color=colors), text=[f"{v:+.2f}" for v in vals], textposition="outside",
                           textfont=dict(size=10), hovertemplate="%{y}: %{x:+.3f} V<extra></extra>"))
    fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(size=11))
    fig.update_xaxes(title="Potential (V)")
    fig.update_layout(showlegend=False)
    return _base(fig, dark, max(380, 24 * len(entries) + 60))


def matrix_plotly(names: list[str], matrix: list[list[float]], dark: bool = True) -> go.Figure:
    z = np.asarray(matrix)
    fig = go.Figure(go.Heatmap(z=z, x=names, y=names, colorscale=[[0, "#2FBF71"], [0.15, "#C8D655"], [0.35, "#F2C14E"], [0.6, "#EF8354"], [1, "#E4572E"]],
                               zmin=0, zmax=max(0.8, float(z.max())), text=np.round(z, 2), texttemplate="%{text}", textfont=dict(size=11, color="#0B1220"),
                               hovertemplate="%{y} / %{x}: ΔE = %{z:.2f} V<extra></extra>", colorbar=dict(title="ΔE (V)")))
    fig.update_yaxes(autorange="reversed")
    return _base(fig, dark, max(360, 56 * len(names) + 90))
