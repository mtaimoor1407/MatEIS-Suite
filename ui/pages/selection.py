"""Theme 2: Materials Selection & Ashby Plotter."""
from __future__ import annotations

from nicegui import ui

from core.exceptions import MatEISError
from core.selection.filters import Constraints, apply_constraints
from core.selection.indices import INDICES, rank_materials
from core.selection.properties import CLASS_COLORS, MATERIAL_CLASSES, PROPERTIES
from core.selection.report import csv_bytes, pdf_report
from ui.components.kit import chip, esc, fmt, ghost_button, metric, notice, panel, primary_button
from ui.figures.selection import ashby_figure
from ui.layout import frame, is_dark
from ui.services import get_services

FILTERS = [("strength", "Strength", "MPa", 10), ("modulus", "Young's modulus", "GPa", 5), ("density", "Density", "Mg/m³", 0.5), ("cost", "Cost", "USD/kg", 1)]
COLUMNS = [
    {"name": "rank", "label": "#", "field": "rank", "align": "left", "sortable": True},
    {"name": "name", "label": "Material", "field": "name", "align": "left", "sortable": True},
    {"name": "cls", "label": "Class", "field": "material_class", "align": "left", "sortable": True},
    {"name": "rho", "label": "ρ (Mg/m³)", "field": "density", "align": "right", "sortable": True},
    {"name": "E", "label": "E (GPa)", "field": "modulus", "align": "right", "sortable": True},
    {"name": "s", "label": "Strength (MPa)", "field": "strength", "align": "right", "sortable": True},
    {"name": "c", "label": "Cost (USD/kg)", "field": "cost", "align": "right", "sortable": True},
    {"name": "m", "label": "Index M", "field": "index_value", "align": "right", "sortable": True},
]


@ui.page("/selection")
def selection_page() -> None:
    svc = get_services()
    dark = is_dark()
    df_all = svc.materials.to_dataframe()
    st: dict = {"ranked": None, "constraints": None, "index": None, "error": None, "busy": False}

    with frame("selection", "Materials selection", "Set design constraints, choose what you want to minimise, and rank the materials with an Ashby performance index.", "selection"):
        if df_all.empty:
            notice("The materials database is empty. Add materials on the Databases page.", "warn")
            return
        with ui.element("div").classes("mx-grid-side"):
            with ui.column().classes("gap-4 w-full"):
                with panel("1. Design constraints", "Leave a box empty for no limit. Limits are inclusive (≥ min, ≤ max).", accent=True):
                    ui.html('<div class="mx-label" style="margin-bottom:6px">Material classes</div>', sanitize=False)
                    classes = ui.select(list(MATERIAL_CLASSES), multiple=True, value=list(MATERIAL_CLASSES)).props("use-chips outlined dense").classes("w-full")
                    boxes: dict[str, tuple] = {}
                    for key, name, unit, step in FILTERS:
                        ui.html(f'<div class="mx-label" style="margin:12px 0 6px">{name} ({unit})</div>', sanitize=False)
                        with ui.row().classes("w-full no-wrap gap-2"):
                            lo = ui.number(placeholder="min", value=None, step=step).props("dense outlined clearable").classes("col")
                            hi = ui.number(placeholder="max", value=None, step=step).props("dense outlined clearable").classes("col")
                        boxes[key] = (lo, hi)
                    ui.html('<div class="mx-label" style="margin:16px 0 6px">Quick presets</div>', sanitize=False)
                    with ui.row().classes("gap-2"):
                        for text, rng in [("Strength ≥ 200 MPa", {"strength": (200, None)}), ("Lightweight: ρ ≤ 3", {"density": (None, 3)}), ("Budget: ≤ 5 USD/kg", {"cost": (None, 5)})]:
                            ui.html(f'<span class="mx-chip click">{esc(text)}</span>', sanitize=False).on("click", lambda _=None, r=rng: preset(r))
                    ghost_button("Reset constraints", lambda: reset(), "restart_alt").classes("q-mt-md")
                with panel("Class colours"):
                    ui.html('<div class="mx-legend">' + "".join(f'<span><i style="background:{c}"></i>{k}</span>' for k, c in CLASS_COLORS.items()) + "</div>", sanitize=False)

            with ui.column().classes("gap-4 w-full min-w-0"):
                with panel("2. Design objective", accent=True):
                    objective = ui.select({k: v.label for k, v in INDICES.items()}, value="stiff_beam").props("outlined dense").classes("w-full")
                    index_info = ui.html("", sanitize=False)
                summary = ui.element("div").classes("mx-grid-3")
                warn_box = ui.column().classes("w-full gap-2")
                with panel(classes="p-3"):
                    with ui.row().classes("items-center justify-between w-full px-2 pt-1"):
                        ui.html('<div class="mx-panel-title">Ashby chart</div>', sanitize=False)
                        with ui.row().classes("items-center gap-3"):
                            axes_mode = ui.toggle({"match": "Match the index", "custom": "Custom axes"}, value="match").props("no-caps dense unelevated toggle-color=none toggle-text-color=none")
                            hulls = ui.checkbox("Class envelopes", value=True)
                    axes_row = ui.row().classes("w-full gap-3 px-2 no-wrap")
                    with axes_row:
                        keys = list(PROPERTIES)
                        x_sel = ui.select({k: PROPERTIES[k].axis_label for k in keys}, value="density", label="X axis").props("outlined dense").classes("col")
                        y_sel = ui.select({k: PROPERTIES[k].axis_label for k in keys}, value="modulus", label="Y axis").props("outlined dense").classes("col")
                    axes_row.set_visibility(False)
                    plot = ui.plotly(ashby_figure(df_all, rank_materials(df_all, INDICES["stiff_beam"]), INDICES["stiff_beam"], "density", "modulus", True, dark)).classes("w-full")
                    ui.html('<div style="color:var(--faint);font-size:12.5px;padding:0 8px 6px">Log-log chart. The dashed line has constant M and passes through the best material; '
                            'points above and to the left of it perform better. Grey points are excluded by the constraints.</div>', sanitize=False)
                table_panel = ui.column().classes("w-full gap-3")

    detail = ui.dialog()

    def read_constraints() -> Constraints:
        ranges = {k: (lo.value, hi.value) for k, (lo, hi) in boxes.items()}
        return Constraints(tuple(classes.value or ()), ranges).validate()

    def clear_boxes() -> None:
        classes.value = list(MATERIAL_CLASSES)
        for lo, hi in boxes.values():
            lo.value = hi.value = None

    def reset() -> None:
        st["busy"] = True
        clear_boxes()
        st["busy"] = False
        update()

    def preset(rng: dict) -> None:
        st["busy"] = True
        clear_boxes()
        for k, (a, b) in rng.items():
            boxes[k][0].value, boxes[k][1].value = a, b
        st["busy"] = False
        update()

    def show_detail(row: dict) -> None:
        detail.clear()
        with detail, ui.card().classes("w-[560px] max-w-full"):
            ui.html(f'<div class="mx-panel-title" style="font-size:20px">{esc(row["name"])}</div>'
                    f'<div style="margin:6px 0 12px;display:flex;gap:8px">{chip(row["material_class"], True)}{chip("rank " + str(row["rank"]))}</div>', sanitize=False)
            with ui.element("div").classes("mx-grid-2"):
                metric("Density", f"{row['density']:.2f}", "Mg/m³")
                metric("Young's modulus", fmt(row["modulus"]), "GPa")
                metric(f"Strength ({row['strength_basis']})", fmt(row["strength"]), "MPa")
                metric("Cost", fmt(row["cost"]), "USD/kg")
                metric("Specific stiffness E/ρ", fmt(row["modulus"] / row["density"]), "GPa·m³/Mg")
                metric("Specific strength σ/ρ", fmt(row["strength"] / row["density"]), "MPa·m³/Mg")
            ui.html(f'<p style="color:var(--soft);margin-top:12px">{esc(row.get("notes") or "")}</p>'
                    f'<p style="color:var(--faint);font-size:13px">Source: {esc(row.get("source") or "—")} · Data verified: {"yes" if row.get("verified") else "not yet"}</p>', sanitize=False)
            ui.button("Close", on_click=detail.close, color=None).classes("mx-ghost").props("no-caps flat")
        detail.open()

    def update(_=None) -> None:
        if st["busy"]:
            return
        index = INDICES[objective.value]
        axes_row.set_visibility(axes_mode.value == "custom")
        index_info.set_content(f'<div style="margin-top:10px;display:flex;gap:10px;flex-wrap:wrap;align-items:center">'
                               f'<span class="mx-chip accent">M = {esc(index.formula)}</span><span class="mx-chip">units: {esc(index.unit)}</span>'
                               f'<span style="color:var(--soft);font-size:14px">{esc(index.use_case)} Higher M is better.</span></div>')
        summary.clear()
        warn_box.clear()
        table_panel.clear()
        try:
            constraints = read_constraints()
        except MatEISError as exc:
            st["error"] = str(exc)
            with warn_box:
                notice(str(exc), "err")
            plot.update_figure(ashby_figure(df_all, rank_materials(df_all.iloc[0:0], index), index, *index.axes, hulls.value, dark))
            return
        st.update(error=None, constraints=constraints, index=index)
        ranked = rank_materials(apply_constraints(df_all, constraints), index)
        st["ranked"] = ranked
        x_key, y_key = index.axes if axes_mode.value == "match" else (x_sel.value, y_sel.value)
        plot.update_figure(ashby_figure(df_all, ranked, index, x_key, y_key, hulls.value, dark))
        with summary:
            if ranked.empty:
                metric("Candidates", f"0 of {len(df_all)}", hint="No material passes")
            else:
                best = ranked.iloc[0]
                metric("Best material", best["name"], hint=f"{best['material_class']}", hot=True)
                metric("Best index value", f"{best['index_value']:.3g}", hint=(f"Runner-up: {ranked.iloc[1]['name']}" if len(ranked) > 1 else "Only candidate"))
                metric("Candidates left", f"{len(ranked)}", f"of {len(df_all)}")
        with warn_box:
            if ranked.empty:
                notice("No material meets every constraint. Relax a limit or add a material class. Grey points show what was excluded.", "warn")
            elif index.numerator == "strength" and (ranked["strength_basis"] != "yield").any():
                notice("Ceramics, brittle polymers and composites have no true yield point; their tensile or flexural strength is used (shown in the details dialog and the CSV). Compare strength rankings across classes with care.")
        if ranked.empty:
            return
        with table_panel:
            with panel("3. Ranked materials", "Click a row for details.", accent=True):
                rows = [{**{k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}, "index_value": round(float(r["index_value"]), 4)}
                        for r in ranked.to_dict("records")]
                table = ui.table(columns=COLUMNS, rows=rows, row_key="name", pagination=10).classes("w-full").props("flat dense")
                table.on("rowClick", lambda e: show_detail(e.args[1]))
            with ui.row().classes("gap-2"):
                primary_button("Download CSV", download_csv, "download")
                ghost_button("PDF report", download_pdf, "picture_as_pdf")
                ghost_button("Save to history", save_history, "bookmark_add")

    def download_csv() -> None:
        ui.download.content(csv_bytes(st["ranked"]), "mateis_ranking.csv", "text/csv")

    def download_pdf() -> None:
        ui.download.content(pdf_report(df_all, st["ranked"], st["index"], st["constraints"]), "mateis_selection_report.pdf", "application/pdf")

    def save_history() -> None:
        r, idx, c = st["ranked"], st["index"], st["constraints"]
        best = r.iloc[0]
        svc.history.add("selection", f"{idx.label}: {best['name']}", {"index": idx.key, "constraints": c.to_dict()},
                        {"best": best["name"], "index_value": float(best["index_value"]), "candidates": int(len(r)),
                         "top3": r.head(3)["name"].tolist()})
        ui.notify("Saved to history.", type="positive")

    for w in (objective, classes, axes_mode, hulls, x_sel, y_sel, *[b for pair in boxes.values() for b in pair]):
        w.on_value_change(update)
    update()
