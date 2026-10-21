"""Landing page: hero, three theme cards, facts."""
from __future__ import annotations

from nicegui import ui

import config
from core.phase.diagrams import get_diagram
from ui.components.kit import esc
from ui.figures.svgs import ashby_svg, diagram_svg, ladder_svg
from ui.layout import frame
from ui.services import get_services


def _card(href: str, theme: str, title: str, blurb: str, bullets: list[str], thumb: str) -> None:
    items = "".join(f"<li>{esc(b)}</li>" for b in bullets)
    ui.html(f'<a class="mx-tcard theme-{theme}" href="{href}"><div class="thumb">{thumb}</div><h3>{esc(title)}</h3>'
            f'<div style="color:var(--soft);font-size:14.5px">{esc(blurb)}</div><ul>{items}</ul>'
            f'<div class="go">Open module <i class="q-icon notranslate material-icons">arrow_forward</i></div></a>', sanitize=False)


@ui.page("/")
def home_page() -> None:
    svc = get_services()
    fe = get_diagram("fe_c")
    eq = fe.equilibrium(0.35, 700)
    df = svc.materials.to_dataframe()
    with frame("home", "Welcome", "", "selection"):
        with ui.element("div").classes("mx-hero"):
            with ui.element("div"):
                ui.html('<div class="mx-label" style="margin-bottom:12px">CSC-214 · Semester project</div>'
                        '<h1 class="mx-display">Three tools for the <em>materials</em> engineer, in one suite.</h1>'
                        '<p>Read phase diagrams with the lever rule, choose materials with Ashby charts, and predict corrosion rate, galvanic risk and protection. '
                        'Every number is calculated by tested Python code and shown with its working.</p>', sanitize=False)
                with ui.row().classes("gap-3"):
                    ui.button("Explore phase diagrams", icon="thermostat", on_click=lambda: ui.navigate.to("/phase"), color=None).classes("mx-primary").props("no-caps unelevated")
                    ui.button("Read the guide", icon="menu_book", on_click=lambda: ui.navigate.to("/guide"), color=None).classes("mx-ghost").props("no-caps flat")
            ui.html(f'<div class="mx-svgbox theme-phase">{diagram_svg(fe, eq, 640, 400)}</div>', sanitize=False)

        ui.html('<div style="height:22px"></div>', sanitize=False)
        with ui.element("div").classes("mx-grid-3"):
            _card("/phase", "phase", "Phase diagrams", "Interactive binary diagrams with lever-rule amounts and predicted microstructure.",
                  ["Fe–Fe₃C, Cu–Ni and Pb–Sn", "Click the diagram to set composition and temperature", "Pearlite vs proeutectoid ferrite, with a schematic"],
                  diagram_svg(get_diagram("pb_sn"), None, 300, 150, labels=False, pad=8, axis_text=False))
            _card("/selection", "selection", "Materials selection", "Rank engineering materials with Ashby performance indices and filter by design constraints.",
                  [f"{len(df)} materials in 4 classes", "9 performance indices with guide lines", "Export ranked results as CSV or PDF"], ashby_svg(df))
            emf = [e.potential_v for e in svc.emf.list("standard")]
            _card("/corrosion", "corrosion", "Corrosion", "Corrosion rate, galvanic compatibility and a protection plan with sacrificial-anode sizing.",
                  ["Weight loss, i_corr, Tafel extrapolation", "EMF and seawater galvanic series", "Coatings, anodes and a PDF recommendation report"], ladder_svg(emf))

        ui.html('<div style="height:26px"></div>', sanitize=False)
        with ui.element("div").classes("mx-grid-4"):
            for big, small in [("3", "complete modules"), (str(len(df)), "materials with cited data"), (str(svc.emf.count()), "EMF and galvanic-series entries"), ("460+", "automated tests")]:
                ui.html(f'<div class="mx-stat"><b class="mx-display">{big}</b><span>{small}</span></div>', sanitize=False)
        ui.html(f'<div style="margin-top:28px;color:var(--faint);font-size:13px">{esc(config.DEPARTMENT)} · Instructor: {esc(config.INSTRUCTOR)}</div>', sanitize=False)
