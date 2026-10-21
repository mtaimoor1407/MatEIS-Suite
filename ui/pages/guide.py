"""Guide page: how to use the suite, theory summary, requirement coverage, team."""
from __future__ import annotations

from nicegui import ui

import config
from ui.components.kit import esc, formula_block, panel, table_html
from ui.layout import frame

REQUIREMENTS = [
    ("GUI application using Python (desktop or web)", "Web GUI built with NiceGUI (Python only), run with: python main.py", "main.py, ui/"),
    ("Theme 1: plot binary phase diagrams (e.g. Fe-C, Cu-Ni) with composition and temperature input", "Fe–Fe₃C, Cu–Ni and Pb–Sn diagrams, sliders, number boxes, click-on-diagram", "Phase diagrams page, core/phase/"),
    ("Theme 1: dynamic lever-rule phase amounts", "Tie-line, compositions and amounts with the working shown", "core/phase/diagram.py"),
    ("Theme 1: microstructure description or schematic (e.g. pearlite vs proeutectoid ferrite)", "Microconstituent percentages plus a generated schematic micrograph", "core/phase/microstructure.py, schematic.py"),
    ("Theme 2: database of at least 15 materials with density, modulus, yield strength, cost", "26 materials in 4 classes, with source column and verification flag", "data/materials_seed.json"),
    ("Theme 2: filters for design constraints (e.g. yield strength > 200 MPa)", "Class and min/max filters for four properties", "core/selection/filters.py"),
    ("Theme 2: interactive two-property plot highlighting the optimal material for a performance index", "Plotly log-log Ashby chart with guide line and starred winner", "ui/figures/selection.py"),
    ("Theme 3: corrosion rate in mm/year or mils/year from weight loss", "ASTM G1/G31 equation, mm/y, mpy and µm/y", "core/corrosion/rates.py"),
    ("Theme 3: corrosion rate from electrochemical / Tafel parameters", "i_corr (Faraday), Tafel extrapolation fit, Stern–Geary", "core/corrosion/rates.py"),
    ("Theme 3: galvanic risk from an interactive EMF series database", "Editable EMF and seawater series, risk score, compatibility matrix", "core/corrosion/emf.py"),
    ("Theme 3: recommendations report (sacrificial anodes, coatings)", "Rule-based protection plan, anode sizing, PDF report", "core/corrosion/protection.py"),
    ("numpy / pandas backend; matplotlib charts embedded", "numpy and pandas in core/, matplotlib view and PDF reports", "core/, Matplotlib tab"),
    ("Local JSON or sqlite3 storage", "SQLite for materials, EMF series and history, seeded from JSON", "core/selection/database.py, core/storage.py"),
    ("OOP code, error handling, boundary-value testing", "Dataclasses and classes, custom exceptions, 460+ pytest tests", "tests/"),
    ("README, user guide, documentation, comments", "README and docs/ folder, docstrings throughout", "README.md, docs/"),
    ("Presentation and demo; video documentation", "Outline, demo script and video script included", "docs/PRESENTATION_OUTLINE.md, VIDEO_SCRIPT.md"),
]


@ui.page("/guide")
def guide_page() -> None:
    with frame("guide", "Guide & requirements", "How to use the suite, the science in brief, and where every requirement of the project document is met.", "selection"):
        with ui.element("div").classes("mx-grid-3"):
            for theme, title, steps in [
                ("phase", "Phase diagrams", ["Choose Fe–Fe₃C, Cu–Ni or Pb–Sn.", "Set composition and temperature, or click the diagram.", "Read phases, amounts and microstructure; export a PDF."]),
                ("selection", "Materials selection", ["Set constraints (e.g. strength ≥ 200 MPa).", "Pick an objective such as light, stiff beam.", "Study the Ashby chart and ranked table; export CSV or PDF."]),
                ("corrosion", "Corrosion", ["Compute a rate from weight loss or electrochemical data.", "Check the galvanic risk of a metal couple.", "Generate the protection plan and report."]),
            ]:
                with ui.element("div").classes(f"mx-panel accent theme-{theme}").style("width:100%"):
                    ui.html(f'<div class="mx-panel-title">{title}</div><ol style="margin:8px 0 0 18px;padding:0;color:var(--soft);line-height:1.7">'
                            + "".join(f"<li>{esc(s)}</li>" for s in steps) + "</ol>", sanitize=False)

        ui.html('<div style="height:8px"></div>', sanitize=False)
        with ui.element("div").classes("mx-grid-3"):
            with panel("Lever rule", "Phase theme", accent=True, classes="theme-phase"):
                formula_block(["W(left) = (C(right) − C₀) / (C(right) − C(left))", "W(right) = (C₀ − C(left)) / (C(right) − C(left))",
                               "Steel below 727 °C:", "W(pearlite) = (C₀ − 0.022) / 0.738", "W(proeutectoid α) = (0.76 − C₀) / 0.738"])
            with panel("Performance indices", "Selection theme", accent=True, classes="theme-selection"):
                formula_block(["Stiff beam: M = E^½ / ρ", "Strong beam: M = σy^⅔ / ρ", "Cost version: replace ρ by Cm·ρ", "Guide-line slope on log–log axes = 1 / p"])
            with panel("Corrosion rate", "Corrosion theme", accent=True, classes="theme-corrosion"):
                formula_block(["Weight loss: CR[mm/y] = 8.76×10⁴ ΔW / (A t ρ)", "Faraday: CR[mm/y] = 3.27×10⁻³ i_corr EW / ρ", "Stern–Geary: i_corr = B / R_p", "mpy = 39.37 × mm/y"])

        with panel("Requirements of the project document and where they are met", accent=True):
            table_html(["Requirement", "How it is met", "Where"], [[esc(a), esc(b), f"<code>{esc(c)}</code>"] for a, b, c in REQUIREMENTS])

        with ui.element("div").classes("mx-grid-2"):
            with panel("Data and accuracy", accent=True):
                ui.html('<ul style="margin:0 0 0 18px;color:var(--soft);line-height:1.7"><li>Material properties are typical textbook values (Callister App. B, MatWeb, Ashby). Each row has a source and a verified flag.</li>'
                        '<li>Phase diagrams are digitised approximations (about ±10 °C, ±1 wt%). Textbook worked examples reproduce exactly.</li>'
                        '<li>EMF values come from Callister Table 17.1 and CRC; the seawater series is a typical mid-range, and real values scatter by ±0.05–0.15 V.</li>'
                        '<li>Corrosion tools assume uniform attack. Pitting, crevice and stress-corrosion cracking are not predicted.</li>'
                        '<li>Protection advice is a screening aid, not a specification.</li></ul>', sanitize=False)
            with panel("Team", accent=True):
                table_html(["Name", "Reg. no.", "Session"], [[esc(n), esc(r), esc(s)] for n, r, s in config.TEAM])
                ui.html(f'<p style="color:var(--faint);font-size:13px;margin-top:10px">{esc(config.COURSE)} · {esc(config.INSTRUCTOR)}<br>{esc(config.DEPARTMENT)}</p>', sanitize=False)
