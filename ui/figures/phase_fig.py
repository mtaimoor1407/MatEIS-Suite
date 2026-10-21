"""Plotly and Matplotlib-styling helpers for the phase-diagram page."""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from core.phase.diagram import Equilibrium, PhaseDiagram, polygon_area


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def phase_plotly(diagram: PhaseDiagram, eq: Equilibrium | None, dark: bool = True) -> go.Figure:
    """Interactive diagram: hover shows the field, a hidden grid makes every point clickable."""
    ink = "#EAF0F8" if dark else "#142033"
    soft = "#9FB0C7" if dark else "#4B5B6E"
    grid = "rgba(150,165,185,.18)"
    fig = go.Figure()
    for r in diagram.regions:
        xs, ys = [p[0] for p in r.polygon] + [r.polygon[0][0]], [p[1] for p in r.polygon] + [r.polygon[0][1]]
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", fill="toself", fillcolor=_rgba(r.color, 0.55 if dark else 0.62),
                                 line=dict(color="rgba(20,30,45,.55)" if not dark else "rgba(230,238,248,.35)", width=1),
                                 hoveron="fills", text=r.name, hoverinfo="text", name=r.name, showlegend=False))
    min_area = 0.004 * diagram.bounding_area()
    ann = []
    for r in diagram.regions:
        if polygon_area(r.polygon) >= min_area:
            x, y = r.label_position
            ann.append(dict(x=x, y=y, text=f"<b>{r.name}</b>", showarrow=False, font=dict(size=13, color=ink)))
    for inv in diagram.invariants:
        fig.add_trace(go.Scatter(x=[inv.x_left, inv.x_right], y=[inv.temperature] * 2, mode="lines",
                                 line=dict(color=ink, width=1.2, dash="dash"), hoverinfo="text",
                                 text=f"{inv.name}: {inv.reaction} at {inv.temperature:g} °C", showlegend=False))
        left = inv.name != "Peritectic"
        ann.append(dict(x=inv.x_left if left else inv.x_right, y=inv.temperature, text=f"{inv.name} {inv.temperature:g} °C", showarrow=False,
                        xanchor="left" if left else "right", yanchor="bottom", font=dict(size=10, color=soft)))
    gx = np.linspace(*diagram.x_range, 100)
    gy = np.linspace(*diagram.t_range, 80)
    X, Y = np.meshgrid(gx, gy)
    fig.add_trace(go.Scatter(x=X.ravel(), y=Y.ravel(), mode="markers", marker=dict(size=12, opacity=0), hoverinfo="none", showlegend=False, name="click-grid"))
    if eq is not None:
        t_eval = eq.effective_temperature if eq.effective_temperature is not None else eq.temperature
        if eq.tie_line:
            fig.add_trace(go.Scatter(x=list(eq.tie_line), y=[t_eval] * 2, mode="lines+markers", line=dict(color="#F0647A", width=3),
                                     marker=dict(size=8, color="#F0647A"), hoverinfo="text", showlegend=False,
                                     text=[f"{eq.phases[0].phase}: {eq.tie_line[0]:.4g}", f"{eq.phases[1].phase}: {eq.tie_line[1]:.4g}"]))
        fig.add_trace(go.Scatter(x=[eq.x, eq.x], y=[diagram.t_range[0], eq.temperature], mode="lines",
                                 line=dict(color="#F0647A", width=1, dash="dot"), hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scatter(x=[eq.x], y=[eq.temperature], mode="markers", showlegend=False,
                                 marker=dict(size=15, color="#FFFFFF", line=dict(color="#F0647A", width=3.5)),
                                 hovertext=f"{eq.x:g} {diagram.x_unit}, {eq.temperature:g} °C: {eq.region.name}", hoverinfo="text"))
    fig.update_xaxes(title=diagram.x_label, range=list(diagram.x_range), gridcolor=grid, zeroline=False, color=soft, showline=True, linecolor=grid, mirror=True)
    fig.update_yaxes(title="Temperature (°C)", range=list(diagram.t_range), gridcolor=grid, zeroline=False, color=soft, showline=True, linecolor=grid, mirror=True)
    fig.update_layout(annotations=ann, height=560, margin=dict(l=10, r=10, t=10, b=10), hovermode="closest", dragmode=False,
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color=soft))
    return fig


def style_mpl(ax, dark: bool) -> None:
    """Make a Matplotlib axes readable on the app's dark or light surface."""
    ink = "#EAF0F8" if dark else "#142033"
    ax.figure.patch.set_alpha(0.0)
    ax.set_facecolor("none")
    for s in ax.spines.values():
        s.set_color(ink)
    ax.tick_params(colors=ink)
    ax.xaxis.label.set_color(ink)
    ax.yaxis.label.set_color(ink)
    ax.title.set_color(ink)
