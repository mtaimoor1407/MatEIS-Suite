"""Theme 1: Phase Diagram Interactive Simulator."""
from __future__ import annotations

import base64
import io

from nicegui import ui

from core.exceptions import MatEISError
from core.phase.diagrams import available_diagrams, get_diagram
from core.phase.microstructure import analyze
from core.phase.plotting import draw_diagram, phase_figure
from core.phase.schematic import render_png
from core.reporting.phase_report import phase_pdf
from ui.components.kit import (
    chip,
    esc,
    formula_block,
    ghost_button,
    notice,
    panel,
    primary_button,
    stacked_bar,
    table_html,
)
from ui.figures.phase_fig import phase_plotly, style_mpl
from ui.layout import frame, is_dark
from ui.services import get_services

SHORT = {"fe_c": "Fe–Fe₃C", "cu_ni": "Cu–Ni", "pb_sn": "Pb–Sn"}
DEFAULTS = {"fe_c": (0.35, 25.0, 0.01), "cu_ni": (35.0, 1250.0, 0.1), "pb_sn": (40.0, 150.0, 0.1)}
EXAMPLES = {
    "fe_c": [("0.35 wt% C, 25 °C", 0.35, 25), ("Eutectoid 0.76, 727 °C", 0.76, 727), ("1.4 wt% C, 25 °C", 1.4, 25),
             ("0.4 wt% C, 760 °C", 0.4, 760), ("3.0 wt% C, 25 °C", 3.0, 25), ("4.30 wt% C, 1200 °C", 4.3, 1200)],
    "cu_ni": [("Textbook: 35 wt% Ni, 1250 °C", 35, 1250), ("50 wt% Ni, 1300 °C", 50, 1300), ("70 wt% Ni, 1100 °C", 70, 1100), ("20 wt% Ni, 1400 °C", 20, 1400)],
    "pb_sn": [("Textbook: 40 wt% Sn, 150 °C", 40, 150), ("Eutectic 61.9 wt% Sn, 25 °C", 61.9, 25), ("40 wt% Sn, 200 °C", 40, 200), ("80 wt% Sn, 25 °C", 80, 25)],
}
PHASE_COLORS = {"L": "#E4572E", "α": "#8BC6A1", "β": "#F2C14E", "γ": "#4F86C6", "δ": "#6A9FB5", "Fe₃C": "#B68DBF"}


def _png_data_uri(png: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(png).decode()


def _bar_color(c) -> str:
    if c.texture == "liquid":
        return "#E4572E"
    return c.color2 if c.texture == "lamellar" and c.color2 else c.color


@ui.page("/phase")
def phase_page() -> None:
    svc = get_services()
    dark = is_dark()
    st: dict = {"key": "fe_c", "eq": None, "micro": None, "error": None, "seed": 7, "busy": False}

    def diagram():
        return get_diagram(st["key"])

    with frame("phase", "Phase diagrams", "Pick a binary system, set a composition and temperature (or click the diagram) to see the phases, "
                                          "the lever-rule amounts and the predicted microstructure.", "phase"):
        with ui.element("div").classes("mx-grid-phase"):
            with ui.column().classes("gap-4 w-full"):
                with panel("1. Alloy", "Move the sliders, type a value, or click anywhere on the diagram.", accent=True):
                    system = ui.toggle({k: SHORT[k] for k in available_diagrams()}, value="fe_c").props("no-caps spread unelevated toggle-color=none toggle-text-color=none").classes("w-full")
                    ui.html('<div style="height:10px"></div>', sanitize=False)
                    x_label = ui.html("", sanitize=False)
                    with ui.row().classes("items-center w-full no-wrap gap-3"):
                        x_slider = ui.slider(min=0, max=6.7, step=0.01, value=0.35).props("label").classes("col")
                        ui.number(value=0.35, step=0.01, format="%.4g").props("dense outlined").classes("w-28").bind_value(x_slider)
                    ui.html('<div class="mx-label" style="margin-top:6px">Temperature (°C)</div>', sanitize=False)
                    with ui.row().classes("items-center w-full no-wrap gap-3"):
                        t_slider = ui.slider(min=0, max=1600, step=1, value=25).props("label").classes("col")
                        ui.number(value=25, step=1, format="%.0f").props("dense outlined").classes("w-28").bind_value(t_slider)
                    ui.html('<div class="mx-label" style="margin:10px 0 6px">Examples</div>', sanitize=False)
                    examples = ui.row().classes("gap-2")
                results = ui.column().classes("w-full gap-3")

            with ui.column().classes("gap-4 w-full min-w-0"):
                with panel(classes="p-3"):
                    with ui.tabs().classes("w-full") as tabs:
                        tab_i = ui.tab("Interactive")
                        ui.tab("Matplotlib view")
                    with ui.tab_panels(tabs, value=tab_i).classes("w-full bg-transparent"):
                        with ui.tab_panel(tab_i).classes("p-0"):
                            plot = ui.plotly(phase_plotly(get_diagram("fe_c"), None, dark)).classes("w-full")
                        with ui.tab_panel("Matplotlib view").classes("p-0"):
                            mpl = ui.matplotlib(figsize=(8, 5.4)).classes("w-full")
                    source = ui.html("", sanitize=False)
                micro_box = ui.column().classes("w-full gap-3")

    def draw_mpl() -> None:
        fig = mpl.figure
        fig.clear()
        ax = fig.add_subplot()
        draw_diagram(ax, diagram(), st["eq"], text_color="#EAF0F8" if dark else "#142033")
        style_mpl(ax, dark)
        fig.tight_layout()
        mpl.update()

    def render_results() -> None:
        results.clear()
        d, eq = diagram(), st["eq"]
        with results:
            if st["error"]:
                notice(st["error"], "err")
                return
            with panel("2. Phases present", f"{eq.x:g} {d.x_unit} at {eq.temperature:g} °C", accent=True):
                ui.html(f'<div style="display:flex;gap:8px;align-items:center;margin-bottom:12px"><span class="mx-label">Phase field</span>{chip(eq.region.name, True)}</div>', sanitize=False)
                stacked_bar([(d.phase_label(p.phase), p.fraction, PHASE_COLORS.get(p.phase, "#999")) for p in eq.phases])
                ui.html('<div style="height:10px"></div>', sanitize=False)
                table_html(["Phase", f"Composition ({d.x_unit})", "Amount (wt%)"],
                           [[esc(d.phase_label(p.phase)), f"{p.composition:.4g}", f"<b>{p.fraction * 100:.2f}</b>"] for p in eq.phases], num_cols=(1, 2))
                for n in eq.notes:
                    notice(n, "warn")
            with panel("3. Lever rule, step by step",
                       "The tie-line is drawn across the two-phase field at the chosen temperature." if eq.tie_line else "Single phase: no tie-line is needed."):
                formula_block(eq.formulas)
            with ui.row().classes("gap-2"):
                primary_button("PDF report", download_pdf, "picture_as_pdf")
                ghost_button("Diagram PNG", download_png, "image")
                ghost_button("Save to history", save_history, "bookmark_add")

    def render_micro() -> None:
        micro_box.clear()
        if st["error"]:
            return
        micro = st["micro"]
        with micro_box:
            with panel("4. Predicted microstructure", "Schematic micrograph for slow (equilibrium) cooling.", accent=True):
                with ui.element("div").classes("mx-grid-2").style("align-items:start"):
                    ui.html(f'<div class="mx-imgbox"><img alt="Schematic microstructure" src="{_png_data_uri(render_png(micro, 520, 340, seed=st["seed"]))}"></div>', sanitize=False)
                    with ui.column().classes("gap-3 w-full"):
                        ui.html(f'<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">{chip(micro.classification, True)}</div>', sanitize=False)
                        stacked_bar([(c.name, c.fraction, _bar_color(c)) for c in micro.constituents])
                        table_html(["Microconstituent", "Amount (wt%)"], [[esc(c.name), f"<b>{c.fraction * 100:.2f}</b>"] for c in micro.constituents], num_cols=(1,))
                ui.html(f'<p style="color:var(--soft);margin:14px 0 4px;font-size:15px">{esc(micro.description)}</p>', sanitize=False)
                if micro.properties:
                    ui.html(f'<p style="color:var(--soft);margin:0 0 8px;font-size:14px"><b style="color:var(--ink)">Typical behaviour:</b> {esc(micro.properties)}</p>', sanitize=False)
                formula_block(micro.formulas)
                for n in micro.notes:
                    notice(n)
                ghost_button("New grain pattern", reroll, "casino")

    def reroll() -> None:
        st["seed"] += 1
        render_micro()

    def recompute() -> None:
        d = diagram()
        try:
            st["eq"] = d.equilibrium(float(x_slider.value), float(t_slider.value))
            st["micro"] = analyze(d, st["eq"])
            st["error"] = None
        except MatEISError as exc:
            st["error"] = str(exc)
        except (TypeError, ValueError):
            st["error"] = "Enter a number for composition and temperature."
        plot.update_figure(phase_plotly(d, None if st["error"] else st["eq"], dark))
        draw_mpl()
        render_results()
        render_micro()

    def set_values(x: float, t: float) -> None:
        st["busy"] = True
        x_slider.value, t_slider.value = x, t
        st["busy"] = False
        recompute()

    def set_system(key: str) -> None:
        st["key"] = key
        d = diagram()
        x0, t0, step = DEFAULTS[key]
        x_slider.props(f"min={d.x_range[0]} max={d.x_range[1]} step={step}")
        t_slider.props(f"min={d.t_range[0]} max={d.t_range[1]} step=1")
        x_label.set_content(f'<div class="mx-label">Composition ({d.x_unit})</div>')
        source.set_content(f'<div style="color:var(--faint);font-size:12.5px;margin-top:6px">{esc(d.title)} · {esc(d.source)} · digitised approximation (±10 °C, ±1 wt%)</div>')
        examples.clear()
        with examples:
            for text, ex, et in EXAMPLES[key]:
                ui.html(f'<span class="mx-chip click">{esc(text)}</span>', sanitize=False).on("click", lambda _=None, a=ex, b=et: set_values(a, b))
        set_values(x0, t0)

    def on_click(e) -> None:
        try:
            pt = e.args["points"][0]
            d = diagram()
            decimals = 2 if st["key"] == "fe_c" else 1
            set_values(round(min(max(float(pt["x"]), d.x_range[0]), d.x_range[1]), decimals),
                       round(min(max(float(pt["y"]), d.t_range[0]), d.t_range[1])))
        except (KeyError, IndexError, TypeError, ValueError):
            pass

    def download_pdf() -> None:
        if st["error"]:
            ui.notify("Fix the input first.", type="warning")
            return
        ui.download.content(phase_pdf(diagram(), st["eq"], st["micro"]), "mateis_phase_report.pdf", "application/pdf")

    def download_png() -> None:
        buf = io.BytesIO()
        phase_figure(diagram(), None if st["error"] else st["eq"]).savefig(buf, format="png")
        ui.download.content(buf.getvalue(), f"mateis_{st['key']}_diagram.png", "image/png")

    def save_history() -> None:
        if st["error"]:
            ui.notify("Nothing to save: fix the input first.", type="warning")
            return
        eq, m, d = st["eq"], st["micro"], diagram()
        svc.history.add("phase", f"{d.title}: {eq.x:g} {d.x_unit}, {eq.temperature:g} °C",
                        {"diagram": st["key"], "composition": eq.x, "temperature_c": eq.temperature},
                        {"field": eq.region.name,
                         "phases": [{"phase": p.phase, "composition": round(p.composition, 4), "wt_fraction": round(p.fraction, 4)} for p in eq.phases],
                         "microstructure": m.classification,
                         "constituents": [{"name": c.name, "wt_fraction": round(c.fraction, 4)} for c in m.constituents]})
        ui.notify("Saved to history.", type="positive")

    def changed(_=None) -> None:
        if not st["busy"]:
            recompute()

    system.on_value_change(lambda e: set_system(e.value))
    x_slider.on_value_change(changed)
    t_slider.on_value_change(changed)
    plot.on("plotly_click", on_click)
    set_system("fe_c")
