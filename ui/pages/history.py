"""History page: saved analyses from all three modules."""
from __future__ import annotations

import json

from nicegui import ui

from ui.components.kit import chip, esc, ghost_button, notice, panel
from ui.layout import frame
from ui.services import get_services

THEME_LABEL = {"phase": "Phase diagram", "selection": "Materials selection", "corrosion": "Corrosion"}
COLS = [
    {"name": "when", "label": "Saved at", "field": "created_at", "align": "left", "sortable": True},
    {"name": "theme", "label": "Module", "field": "theme_label", "align": "left", "sortable": True},
    {"name": "title", "label": "Analysis", "field": "title", "align": "left"},
]


@ui.page("/history")
def history_page() -> None:
    svc = get_services()
    with frame("history", "History", "Every analysis you saved with 'Save to history', stored in SQLite.", "selection"):
        with ui.row().classes("items-center gap-3 w-full"):
            flt = ui.select({"": "All modules", **THEME_LABEL}, value="", label="Show").props("outlined dense").classes("w-56")
            ghost_button("Clear shown", lambda: clear(), "delete_sweep")
        area = ui.column().classes("w-full gap-3")

    detail = ui.dialog()

    def show(entry: dict) -> None:
        detail.clear()
        with detail, ui.card().classes("w-[680px] max-w-full"):
            ui.html(f'<div class="mx-panel-title" style="font-size:19px">{esc(entry["title"])}</div>'
                    f'<div style="margin:6px 0 10px;display:flex;gap:8px">{chip(THEME_LABEL[entry["theme"]], True)}{chip(entry["created_at"])}</div>', sanitize=False)
            ui.html('<div class="mx-label">Inputs</div>', sanitize=False)
            ui.html(f'<pre class="mx-formula">{esc(json.dumps(entry["inputs"], indent=2, ensure_ascii=False))}</pre>', sanitize=False)
            ui.html('<div class="mx-label">Results</div>', sanitize=False)
            ui.html(f'<pre class="mx-formula">{esc(json.dumps(entry["results"], indent=2, ensure_ascii=False))}</pre>', sanitize=False)
            with ui.row().classes("justify-end w-full gap-2"):
                ghost_button("Delete", lambda: (svc.history.delete(entry["id"]), detail.close(), render()), "delete")
                ghost_button("Close", detail.close)
        detail.open()

    def render() -> None:
        area.clear()
        entries = svc.history.list(flt.value or None)
        with area:
            if not entries:
                notice("Nothing saved yet. Use 'Save to history' on any module to keep a record of an analysis.")
                return
            rows = [{**e, "theme_label": THEME_LABEL[e["theme"]]} for e in entries]
            with panel(f"{len(entries)} saved analyses", "Click a row to see the inputs and results.", accent=True):
                t = ui.table(columns=COLS, rows=rows, row_key="id", pagination=15).classes("w-full").props("flat dense")
                t.on("rowClick", lambda e: show(svc.history.get(e.args[1]["id"])))

    def clear() -> None:
        svc.history.clear(flt.value or None)
        ui.notify("History cleared.", type="positive")
        render()

    flt.on_value_change(lambda _: render())
    render()
