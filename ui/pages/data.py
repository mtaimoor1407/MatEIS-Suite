"""Databases page: manage materials, EMF / galvanic series and view corrosion material data."""
from __future__ import annotations

from nicegui import ui

import config
from core.corrosion.emf import SERIES, Electrode
from core.corrosion.materials import MATERIALS
from core.exceptions import MatEISError
from core.selection.material import Material
from core.selection.properties import MATERIAL_CLASSES, STRENGTH_BASES
from ui.components.kit import esc, ghost_button, notice, panel, primary_button, table_html
from ui.layout import frame
from ui.services import get_services

MAT_COLS = [
    {"name": "name", "label": "Material", "field": "name", "align": "left", "sortable": True},
    {"name": "cls", "label": "Class", "field": "material_class", "align": "left", "sortable": True},
    {"name": "rho", "label": "ρ (kg/m³)", "field": "density_kg_m3", "align": "right", "sortable": True},
    {"name": "E", "label": "E (GPa)", "field": "youngs_modulus_gpa", "align": "right", "sortable": True},
    {"name": "s", "label": "Strength (MPa)", "field": "yield_strength_mpa", "align": "right", "sortable": True},
    {"name": "b", "label": "Basis", "field": "strength_basis", "align": "left"},
    {"name": "c", "label": "Cost (USD/kg)", "field": "cost_usd_per_kg", "align": "right", "sortable": True},
    {"name": "v", "label": "Verified", "field": "verified_text", "align": "center"},
    {"name": "src", "label": "Source", "field": "source", "align": "left"},
]
EMF_COLS = [
    {"name": "name", "label": "Metal", "field": "name", "align": "left", "sortable": True},
    {"name": "v", "label": "Potential (V)", "field": "potential_v", "align": "right", "sortable": True},
    {"name": "r", "label": "Half-reaction", "field": "half_reaction", "align": "left"},
    {"name": "src", "label": "Source", "field": "source", "align": "left"},
    {"name": "cu", "label": "Custom", "field": "custom_text", "align": "center"},
]


@ui.page("/data")
def data_page() -> None:
    svc = get_services()
    st = {"mat": None, "emf": None}

    with frame("data", "Databases", "Browse, add, edit and verify the data behind every calculation. Changes are stored in SQLite.", "selection"):
        with ui.tabs().classes("w-full") as tabs:
            t_mat = ui.tab("Materials (Ashby)")
            t_emf = ui.tab("EMF and galvanic series")
            t_cor = ui.tab("Corrosion materials")
        with ui.tab_panels(tabs, value=t_mat).classes("w-full bg-transparent"):
            with ui.tab_panel(t_mat).classes("p-0 pt-4"):
                mat_area = ui.column().classes("w-full gap-3")
            with ui.tab_panel(t_emf).classes("p-0 pt-4"):
                emf_area = ui.column().classes("w-full gap-3")
            with ui.tab_panel(t_cor).classes("p-0 pt-4"):
                with panel("Metals and alloys for corrosion calculations", "Density and equivalent weight (EW = 1 / Σ n·f / W) used by the corrosion rate tools.", accent=True):
                    table_html(["Material", "Family", "Density (g/cm³)", "Equivalent weight", "Composition (mass fraction)"],
                               [[esc(m.name), esc(m.family), f"{m.density:g}", f"{m.equivalent_weight:.2f}",
                                 esc(", ".join(f"{k} {v:g}" for k, v in m.composition.items()))] for m in MATERIALS.values()], num_cols=(2, 3))

    # ------------------------------------------------------------ materials
    dlg = ui.dialog()

    def material_form(existing: Material | None) -> None:
        dlg.clear()
        with dlg, ui.card().classes("w-[620px] max-w-full gap-2"):
            ui.html(f'<div class="mx-panel-title" style="font-size:19px">{"Edit" if existing else "Add"} material</div>', sanitize=False)
            name = ui.input("Name", value=existing.name if existing else "").props("outlined dense").classes("w-full")
            with ui.row().classes("w-full no-wrap gap-2"):
                cls = ui.select(list(MATERIAL_CLASSES), label="Class", value=existing.material_class if existing else "Metal").props("outlined dense").classes("col")
                basis = ui.select(list(STRENGTH_BASES), label="Strength basis", value=existing.strength_basis if existing else "yield").props("outlined dense").classes("col")
            with ui.row().classes("w-full no-wrap gap-2"):
                rho = ui.number("Density (kg/m³)", value=existing.density_kg_m3 if existing else None).props("outlined dense").classes("col")
                e = ui.number("Young's modulus (GPa)", value=existing.youngs_modulus_gpa if existing else None).props("outlined dense").classes("col")
            with ui.row().classes("w-full no-wrap gap-2"):
                s = ui.number("Strength (MPa)", value=existing.yield_strength_mpa if existing else None).props("outlined dense").classes("col")
                c = ui.number("Cost (USD/kg)", value=existing.cost_usd_per_kg if existing else None).props("outlined dense").classes("col")
            src = ui.input("Source (book, page or URL)", value=existing.source if existing else "").props("outlined dense").classes("w-full")
            notes = ui.textarea("Notes", value=existing.notes if existing else "").props("outlined dense rows=2").classes("w-full")
            verified = ui.checkbox("Verified against the cited source", value=existing.verified if existing else False)
            err = ui.column().classes("w-full")

            def save() -> None:
                err.clear()
                try:
                    m = Material(name=name.value, material_class=cls.value, density_kg_m3=rho.value, youngs_modulus_gpa=e.value,
                                 yield_strength_mpa=s.value, cost_usd_per_kg=c.value, strength_basis=basis.value, source=src.value,
                                 notes=notes.value, verified=verified.value)
                    (svc.materials.update(existing.id, m) if existing else svc.materials.add(m))
                except MatEISError as exc:
                    with err:
                        notice(str(exc), "err")
                    return
                dlg.close()
                ui.notify("Saved.", type="positive")
                render_materials()

            with ui.row().classes("justify-end w-full gap-2"):
                ghost_button("Cancel", dlg.close)
                primary_button("Save", save, "save")
        dlg.open()

    def render_materials() -> None:
        mat_area.clear()
        mats = svc.materials.list_materials()
        rows = [{**m.to_dict(), "verified_text": "✓" if m.verified else "—"} for m in mats]
        with mat_area:
            n_ver = sum(m.verified for m in mats)
            with ui.row().classes("items-center justify-between w-full gap-2"):
                ui.html(f'<div style="color:var(--soft)">{len(mats)} materials · {n_ver} verified against a reference</div>', sanitize=False)
                with ui.row().classes("gap-2"):
                    primary_button("Add material", lambda: material_form(None), "add")
                    ghost_button("Edit selected", lambda: edit_selected(), "edit")
                    ghost_button("Toggle verified", lambda: toggle_verified(), "verified")
                    ghost_button("Delete selected", lambda: delete_selected(), "delete")
                    ghost_button("Reset to original", lambda: reset_materials(), "restore")
            table = ui.table(columns=MAT_COLS, rows=rows, row_key="id", selection="single", pagination=12).classes("w-full").props("flat dense")
            table.on_select(lambda ev: st.update(mat=ev.selection[0] if ev.selection else None))
            st["mat"] = None
            notice("Values are typical textbook figures. Check each row against its cited reference, then tick 'Verified'. Ceramics use flexural strength; some polymers and composites use tensile strength.")

    def edit_selected() -> None:
        if not st["mat"]:
            ui.notify("Select a row first.", type="warning")
            return
        material_form(svc.materials.get(st["mat"]["id"]))

    def toggle_verified() -> None:
        if not st["mat"]:
            ui.notify("Select a row first.", type="warning")
            return
        m = svc.materials.get(st["mat"]["id"])
        svc.materials.set_verified(m.id, not m.verified)
        render_materials()

    def delete_selected() -> None:
        if not st["mat"]:
            ui.notify("Select a row first.", type="warning")
            return
        target = st["mat"]
        with ui.dialog() as confirm, ui.card():
            ui.label(f"Delete '{target['name']}'? This cannot be undone.")
            with ui.row().classes("justify-end w-full gap-2"):
                ghost_button("Cancel", confirm.close)
                primary_button("Delete", lambda: (svc.materials.delete(target["id"]), confirm.close(), render_materials(), ui.notify("Deleted.", type="positive")), "delete")
        confirm.open()

    def reset_materials() -> None:
        with ui.dialog() as confirm, ui.card():
            ui.label("Replace every material with the original dataset? Saved history is kept.")
            with ui.row().classes("justify-end w-full gap-2"):
                ghost_button("Cancel", confirm.close)
                primary_button("Reset", lambda: (svc.materials.seed_from_json(config.MATERIALS_SEED, replace=True), confirm.close(), render_materials(), ui.notify("Reset.", type="positive")), "restore")
        confirm.open()

    # ------------------------------------------------------------ EMF
    def emf_form(existing: Electrode | None) -> None:
        dlg.clear()
        with dlg, ui.card().classes("w-[560px] max-w-full gap-2"):
            ui.html(f'<div class="mx-panel-title" style="font-size:19px">{"Edit" if existing else "Add"} entry</div>', sanitize=False)
            series = ui.select({k: v for k, v in SERIES.items()}, label="Series", value=existing.series if existing else "standard").props("outlined dense").classes("w-full")
            name = ui.input("Metal or alloy", value=existing.name if existing else "").props("outlined dense").classes("w-full")
            pot = ui.number("Potential (V)", value=existing.potential_v if existing else None, step=0.01).props("outlined dense").classes("w-full")
            reaction = ui.input("Half-reaction (optional)", value=existing.half_reaction if existing else "").props("outlined dense").classes("w-full")
            src = ui.input("Source", value=existing.source if existing else "").props("outlined dense").classes("w-full")
            err = ui.column().classes("w-full")

            def save() -> None:
                err.clear()
                try:
                    e = Electrode(name.value, pot.value, series.value, reaction.value or "", src.value or "", existing.notes if existing else "", True)
                    (svc.emf.update(existing.id, e) if existing else svc.emf.add(e))
                except MatEISError as exc:
                    with err:
                        notice(str(exc), "err")
                    return
                dlg.close()
                ui.notify("Saved.", type="positive")
                render_emf()

            with ui.row().classes("justify-end w-full gap-2"):
                ghost_button("Cancel", dlg.close)
                primary_button("Save", save, "save")
        dlg.open()

    def render_emf() -> None:
        emf_area.clear()
        with emf_area:
            with ui.row().classes("items-center justify-between w-full gap-2"):
                ui.html(f'<div style="color:var(--soft)">{svc.emf.count("standard")} EMF entries · {svc.emf.count("seawater")} galvanic-series entries</div>', sanitize=False)
                with ui.row().classes("gap-2"):
                    primary_button("Add entry", lambda: emf_form(None), "add")
                    ghost_button("Edit selected", lambda: edit_emf(), "edit")
                    ghost_button("Delete selected", lambda: delete_emf(), "delete")
                    ghost_button("Reset to original", lambda: reset_emf(), "restore")
            for key, title in SERIES.items():
                with panel(title, "Most active (negative) metals first.", accent=True):
                    rows = [{**e.__dict__, "custom_text": "yes" if e.custom else ""} for e in svc.emf.list(key)]
                    t = ui.table(columns=EMF_COLS, rows=rows, row_key="id", selection="single", pagination=10).classes("w-full").props("flat dense")
                    t.on_select(lambda ev: st.update(emf=ev.selection[0] if ev.selection else None))
            st["emf"] = None

    def edit_emf() -> None:
        if not st["emf"]:
            ui.notify("Select a row first.", type="warning")
            return
        emf_form(svc.emf.get(st["emf"]["id"]))

    def delete_emf() -> None:
        if not st["emf"]:
            ui.notify("Select a row first.", type="warning")
            return
        svc.emf.delete(st["emf"]["id"])
        ui.notify("Deleted.", type="positive")
        render_emf()

    def reset_emf() -> None:
        svc.emf.seed_from_json(config.EMF_SEED, replace=True)
        ui.notify("Reset.", type="positive")
        render_emf()

    render_materials()
    render_emf()
