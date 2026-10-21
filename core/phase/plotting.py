"""Matplotlib rendering of phase diagrams (used in the app's Matplotlib view and in PDF reports)."""
from __future__ import annotations

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.patches import Polygon

from core.phase.diagram import Equilibrium, PhaseDiagram, polygon_area


def draw_diagram(ax, diagram: PhaseDiagram, eq: Equilibrium | None = None, text_color: str = "#1B2430") -> None:
    """Draw the diagram on an existing Axes."""
    for region in diagram.regions:
        ax.add_patch(Polygon(region.polygon, closed=True, facecolor=region.color, alpha=0.55,
                             edgecolor="#2B3138", linewidth=0.8))
    for inv in diagram.invariants:
        ax.plot([inv.x_left, inv.x_right], [inv.temperature, inv.temperature], color="#2B3138", lw=1.2, ls="--")
        ax.text(inv.x_right, inv.temperature, f" {inv.name} {inv.temperature:g} °C", fontsize=6.5, va="bottom", ha="right", color=text_color)
    min_area = 0.004 * diagram.bounding_area()
    for region in diagram.regions:
        if polygon_area(region.polygon) >= min_area:
            x, y = region.label_position
            ax.text(x, y, region.name, ha="center", va="center", fontsize=8, weight="bold", color=text_color)
    if eq is not None:
        t_eval = eq.effective_temperature or eq.temperature
        if eq.tie_line:
            ax.plot(eq.tie_line, [t_eval] * 2, color="#D12F2F", lw=1.6)
            ax.scatter(eq.tie_line, [t_eval] * 2, s=22, color="#D12F2F", zorder=5)
        ax.scatter([eq.x], [eq.temperature], s=70, color="#FFFFFF", edgecolor="#D12F2F", linewidth=2, zorder=6)
        ax.axvline(eq.x, color="#D12F2F", lw=0.8, ls=":")
    ax.set_xlim(*diagram.x_range)
    ax.set_ylim(*diagram.t_range)
    ax.set_xlabel(diagram.x_label)
    ax.set_ylabel("Temperature (°C)")
    ax.set_title(diagram.title, fontsize=11)
    ax.grid(alpha=0.2)


def phase_figure(diagram: PhaseDiagram, eq: Equilibrium | None = None, size: tuple[float, float] = (8, 5.6)) -> Figure:
    fig = Figure(figsize=size, dpi=110)
    FigureCanvasAgg(fig)
    draw_diagram(fig.subplots(), diagram, eq)
    fig.tight_layout()
    return fig
