"""Matplotlib figures for the corrosion tools (used in PDF reports)."""
from __future__ import annotations

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from core.corrosion.emf import Electrode
from core.corrosion.rates import TafelFit


def tafel_figure(potentials, currents, e_corr: float, fit: TafelFit | None = None, window=(0.05, 0.25)) -> Figure:
    """Evans diagram: E against log|i| with the fitted Tafel lines and their intersection."""
    fig = Figure(figsize=(7, 4.6), dpi=110)
    FigureCanvasAgg(fig)
    ax = fig.subplots()
    e, i = np.asarray(potentials, float), np.abs(np.asarray(currents, float))
    ok = i > 0
    eta = e - e_corr
    ax.semilogx(i[ok], e[ok], ".", color="#8EA0B8", ms=4, label="Polarization data")
    sel = ok & (np.abs(eta) >= window[0]) & (np.abs(eta) <= window[1])
    ax.semilogx(i[sel], e[sel], "o", color="#2F6FB5", ms=4, label="Points used for the fit")
    if fit:
        lo, hi = np.log10(max(i[ok].min(), 1e-12)), np.log10(i[ok].max())
        lx = np.linspace(min(lo, np.log10(fit.i_corr)) - 0.2, hi, 50)
        ax.semilogx(10 ** lx, fit.a_anodic + fit.beta_a * lx, "-", color="#E4572E", lw=1.3, label=f"Anodic Tafel (βa = {fit.beta_a * 1000:.0f} mV/dec)")
        ax.semilogx(10 ** lx, fit.a_cathodic - fit.beta_c * lx, "-", color="#2FBFA5", lw=1.3, label=f"Cathodic Tafel (βc = {fit.beta_c * 1000:.0f} mV/dec)")
        ax.plot([fit.i_corr], [fit.e_corr_fit], "*", color="#D12F2F", ms=14, zorder=5, label=f"i_corr = {fit.i_corr * 1e6:.3g} µA/cm²")
    ax.set_xlabel("|Current density| (A/cm²)")
    ax.set_ylabel("Potential (V)")
    ax.set_title("Tafel extrapolation")
    ax.grid(alpha=0.25, which="both")
    ax.legend(fontsize=7)
    fig.tight_layout()
    return fig


def ladder_figure(entries: list[Electrode], highlight: tuple[str, str] | None = None, title: str = "") -> Figure:
    """Horizontal bar ladder of potentials, most active at the bottom."""
    fig = Figure(figsize=(7, max(4.0, 0.22 * len(entries) + 1.2)), dpi=110)
    FigureCanvasAgg(fig)
    ax = fig.subplots()
    names = [e.name for e in entries]
    vals = [e.potential_v for e in entries]
    colors = ["#D12F2F" if highlight and n in highlight else "#8EA0B8" for n in names]
    ax.barh(range(len(names)), vals, color=colors, height=0.7)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=7)
    ax.axvline(0, color="#2B3138", lw=0.8)
    ax.set_xlabel("Potential (V)")
    ax.set_title(title or "Potential series", fontsize=10)
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    return fig
