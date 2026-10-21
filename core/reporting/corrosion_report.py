"""PDF report for the corrosion tools (Theme 3): rate, galvanic risk, protection plan."""
from __future__ import annotations

import io
from datetime import datetime

from matplotlib.backends.backend_pdf import PdfPages

from core.corrosion.emf import GalvanicAssessment
from core.corrosion.plotting import ladder_figure, tafel_figure
from core.corrosion.protection import AnodeDesign, Recommendation
from core.corrosion.rates import RateResult
from core.reporting import pdf_utils as pu


def corrosion_pdf(material_name: str, environment: str, life_years: float, rate: RateResult | None = None,
                  tafel: dict | None = None, galvanic: GalvanicAssessment | None = None, ladder_entries=None,
                  recommendations: list[Recommendation] | None = None, anode: AnodeDesign | None = None) -> bytes:
    """Build the report. Any section whose input is None is left out."""
    buffer = io.BytesIO()
    with PdfPages(buffer) as pdf:
        page = pu.new_page()
        y = pu.header(page, "MatEIS – Corrosion Assessment Report", f"Generated {datetime.now():%Y-%m-%d %H:%M}")
        y = pu.wrapped(page, 0.08, y - 0.01, f"Material: {material_name}\nEnvironment: {environment}\nRequired service life: {life_years:g} years", size=10.5)
        if rate:
            page.text(0.08, y - 0.02, "1. Corrosion rate", fontsize=12.5, weight="bold", color=pu.INK)
            y -= 0.05
            y = pu.wrapped(page, 0.08, y, f"Method: {rate.method}\nRate: {rate.mm_per_year:.4g} mm/year  =  {rate.mpy:.4g} mpy  =  {rate.um_per_year:.4g} µm/year\n"
                                         f"Relative resistance: {rate.rating}. {rate.rating_text}", size=9.5)
            for f in rate.formulas:
                y = pu.wrapped(page, 0.09, y - 0.004, f, width=100, size=8, color=pu.MUTED)
            y = pu.wrapped(page, 0.08, y - 0.01, f"Metal lost over {life_years:g} years at this rate: {rate.mm_per_year * life_years:.3g} mm per exposed face.", size=9.5)
        if tafel:
            fig = tafel_figure(tafel["potentials"], tafel["currents"], tafel["e_corr"], tafel["fit"], tafel.get("window", (0.05, 0.25)))
            pu.embed_figure(page, fig, [0.10, 0.06, 0.80, 0.40] if y > 0.5 else [0.10, 0.05, 0.8, 0.3])
        pu.footer(page, "Rates assume uniform corrosion at a constant rate. Localized attack (pitting, crevice, stress corrosion) is not predicted.")
        pdf.savefig(page)

        if galvanic:
            page = pu.new_page()
            y = pu.header(page, "2. Galvanic corrosion risk", f"{galvanic.anode.name}  +  {galvanic.cathode.name}")
            y = pu.wrapped(page, 0.08, y - 0.01, f"Risk: {galvanic.level.upper()}   (score {galvanic.score:.2f})   ΔE = {galvanic.delta_e:.2f} V\n"
                                                f"Anode (corrodes): {galvanic.anode.name}    Cathode (protected): {galvanic.cathode.name}", size=10.5)
            for line in galvanic.explanation:
                y = pu.wrapped(page, 0.08, y - 0.004, "• " + line, width=100, size=9)
            y = pu.wrapped(page, 0.08, y - 0.015, "Mitigation", size=11, weight="bold")
            for line in galvanic.mitigations:
                y = pu.wrapped(page, 0.08, y - 0.003, "• " + line, width=100, size=9)
            if ladder_entries:
                fig = ladder_figure(ladder_entries, (galvanic.anode.name, galvanic.cathode.name), "Position of the couple in the series")
                pu.embed_figure(page, fig, [0.08, 0.05, 0.84, 0.42 if y > 0.55 else 0.35])
            pu.footer(page, "Risk score combines potential difference, electrolyte conductivity and area ratio. It is qualitative.")
            pdf.savefig(page)

        if recommendations:
            page = pu.new_page()
            y = pu.header(page, "3. Protection recommendations", f"{material_name} in {environment}, {life_years:g}-year life")
            tags = {1: "PRIMARY", 2: "SUPPORTING", 3: "CONSIDER"}
            for r in recommendations:
                if y < 0.12:
                    pdf.savefig(page)
                    page = pu.new_page()
                    y = pu.header(page, "Protection recommendations (continued)")
                y = pu.wrapped(page, 0.08, y - 0.008, f"[{tags[r.priority]}] {r.category}: {r.title}", width=96, size=9.5, weight="bold")
                y = pu.wrapped(page, 0.10, y, r.why, width=100, size=8.5, color=pu.MUTED)
                for d in r.details:
                    y = pu.wrapped(page, 0.11, y, "– " + d, width=100, size=8.5, color=pu.MUTED)
            if anode:
                if y < 0.25:
                    pdf.savefig(page)
                    page = pu.new_page()
                    y = pu.header(page, "Sacrificial anode sizing")
                y = pu.wrapped(page, 0.08, y - 0.02, f"Sacrificial anode design – {anode.anode.name}", size=11, weight="bold")
                for f in anode.formulas:
                    y = pu.wrapped(page, 0.10, y, f, width=100, size=8.5)
                y = pu.wrapped(page, 0.10, y - 0.005, "Indicative mass-based sizing only. Final design needs anode resistance, current output and distribution checks (DNV-RP-B401, NACE SP0176).",
                               width=100, size=8, color=pu.MUTED)
            pu.footer(page, "Screening recommendations. Confirm against ISO 12944, NACE SP0169 and manufacturer data before specifying.")
            pdf.savefig(page)
    return buffer.getvalue()
