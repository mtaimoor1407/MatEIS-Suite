"""Shared page frame: header, navigation drawer, dark-mode toggle."""
from __future__ import annotations

from contextlib import contextmanager

from nicegui import app, ui

import config

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700&family=Hanken+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">'
         '<link rel="stylesheet" href="/static/theme.css">')

NAV = [
    ("section", "Overview"),
    ("home", "Home", "/", "home", "var(--steel)"),
    ("section", "Modules"),
    ("phase", "Phase diagrams", "/phase", "thermostat", "var(--heat)"),
    ("selection", "Materials selection", "/selection", "bubble_chart", "var(--steel)"),
    ("corrosion", "Corrosion", "/corrosion", "water_drop", "var(--verd)"),
    ("section", "Workspace"),
    ("data", "Databases", "/data", "storage", "var(--soft)"),
    ("history", "History", "/history", "history", "var(--soft)"),
    ("guide", "Guide & requirements", "/guide", "menu_book", "var(--soft)"),
]


def is_dark() -> bool:
    return bool(app.storage.user.get("dark", True))


def _toggle_dark() -> None:
    app.storage.user["dark"] = not is_dark()
    ui.navigate.reload()


@contextmanager
def frame(active: str, title: str, subtitle: str = "", theme: str | None = None):
    """Build header + drawer and yield the page content column."""
    ui.add_head_html(FONTS)
    ui.dark_mode(is_dark())
    ui.colors(primary="#5AA9FF", secondary="#2FBFA5", accent="#F2B84B")

    with ui.header().classes("mx-header items-center justify-between px-4").props("elevated=false"):
        with ui.row().classes("items-center gap-3"):
            drawer_btn = ui.button(icon="menu").props("flat round dense").classes("lt-md")
            ui.html('<a class="mx-brand" href="/">Mat<b>EIS</b></a>', sanitize=False)
            ui.html(f'<span class="mx-label gt-xs" style="margin-left:6px">{config.APP_TAGLINE}</span>', sanitize=False)
        with ui.row().classes("items-center gap-2"):
            ui.button(icon="light_mode" if is_dark() else "dark_mode", on_click=_toggle_dark).props("flat round dense").tooltip("Toggle light / dark")

    with ui.left_drawer(value=True, bordered=False).classes("mx-drawer p-0").props("width=250 breakpoint=1000") as drawer:
        drawer_btn.on_click(drawer.toggle)
        ui.html('<div style="height:10px"></div>', sanitize=False)
        for item in NAV:
            if item[0] == "section":
                ui.html(f'<div class="mx-nav-section">{item[1]}</div>', sanitize=False)
                continue
            key, name, href, icon, color = item
            ui.html(f'<a class="mx-nav-link {"active" if key == active else ""}" href="{href}" style="--nav-accent:{color}">'
                    f'<i class="q-icon notranslate material-icons">{icon}</i>{name}</a>', sanitize=False)
        ui.html(f'<div style="position:absolute;bottom:14px;left:24px;right:16px;font-size:12px;color:var(--faint);line-height:1.5">'
                f'{config.COURSE}<br>{config.INSTRUCTOR}</div>', sanitize=False)

    with ui.element("div").classes(f"mx-page theme-{theme or 'selection'}") as page:
        with ui.element("div").classes("mx-page-head"):
            with ui.element("div"):
                ui.html(f'<h1 class="mx-page-title"><span class="dot"></span>{title}</h1>', sanitize=False)
                if subtitle:
                    ui.html(f'<div class="mx-page-sub">{subtitle}</div>', sanitize=False)
        yield page
