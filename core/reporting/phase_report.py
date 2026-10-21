"""PDF report for a phase-diagram analysis (Theme 1)."""
from __future__ import annotations

import io
from datetime import datetime

import matplotlib.image as mpimg
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure

from core.phase.diagram import Equilibrium, PhaseDiagram
from core.phase.microstructure import Microstructure
from core.phase.plotting import phase_figure
from core.phase.schematic import render_png
from core.reporting import pdf_utils as pu


def phase_pdf(diagram: PhaseDiagram, eq: Equilibrium, micro: Microstructure) -> bytes:
    buffer = io.BytesIO()
    with PdfPages(buffer) as pdf:
        page = pu.new_page()
        y = pu.header(page, "MatEIS – Phase Diagram Report", f"{diagram.title} · generated {datetime.now():%Y-%m-%d %H:%M}")
        y = pu.wrapped(page, 0.08, y - 0.01, f"Alloy: {eq.x:g} {diagram.x_unit}  ·  Temperature: {eq.temperature:g} °C\n"
                       f"Phase field: {eq.region.name}", size=10)
        pu.embed_figure(page, phase_figure(diagram, eq), [0.06, 0.50, 0.88, 0.36])
        y = 0.48
        page.text(0.08, y, "Phases present (lever rule)", fontsize=11, weight="bold", color=pu.INK)
        y -= 0.025
        for p in eq.phases:
            page.text(0.10, y, f"{diagram.phase_label(p.phase):<38s} composition {p.composition:8.4g} wt%    amount {p.fraction * 100:6.2f} wt%",
                      fontsize=8.5, family="monospace", color=pu.INK)
            y -= 0.02
        y -= 0.01
        for line in eq.formulas + eq.notes:
            y = pu.wrapped(page, 0.08, y, line, width=105, size=8, color=pu.MUTED)
        pu.footer(page, f"Source of diagram data: {diagram.source}. Digitised approximation (about ±10 °C, ±1 wt%); verify against your textbook.")
        pdf.savefig(page)

        page2 = pu.new_page()
        y = pu.header(page2, "Predicted microstructure", f"{micro.classification}")
        img_fig = Figure(figsize=(6, 4))
        ax = img_fig.add_axes([0, 0, 1, 1])
        ax.imshow(mpimg.imread(io.BytesIO(render_png(micro, 600, 400)), format="png"))
        ax.axis("off")
        pu.embed_figure(page2, img_fig, [0.12, 0.52, 0.76, 0.34])
        y = 0.50
        page2.text(0.08, y, "Microconstituents (slow cooling)", fontsize=11, weight="bold", color=pu.INK)
        y -= 0.025
        for c in micro.constituents:
            page2.text(0.10, y, f"{c.name:<48s} {c.fraction * 100:6.2f} wt%", fontsize=8.5, family="monospace", color=pu.INK)
            y -= 0.02
        y = pu.wrapped(page2, 0.08, y - 0.01, micro.description, size=9)
        if micro.properties:
            y = pu.wrapped(page2, 0.08, y - 0.005, "Typical behaviour: " + micro.properties, size=9, color=pu.MUTED)
        for line in micro.formulas + micro.notes:
            y = pu.wrapped(page2, 0.08, y - 0.004, line, width=105, size=8, color=pu.MUTED)
        pu.footer(page2, "Schematic only: grain shapes are illustrative. Fractions assume equilibrium (slow) cooling.")
        pdf.savefig(page2)
    return buffer.getvalue()
