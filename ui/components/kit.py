"""Small reusable UI building blocks (panels, metrics, bars, notices)."""
from __future__ import annotations

import html
import math
from contextlib import contextmanager

from nicegui import ui

from core.corrosion.rates import RATINGS


def esc(text) -> str:
    return html.escape(str(text))


@contextmanager
def panel(title: str | None = None, subtitle: str | None = None, accent: bool = False, classes: str = ""):
    """Bordered content panel with an optional title block."""
    with ui.element("div").classes(f"mx-panel {'accent' if accent else ''} {classes}") as box:
        if title:
            ui.html(f'<div class="mx-panel-title">{esc(title)}</div>', sanitize=False)
        if subtitle:
            ui.html(f'<div class="mx-panel-sub">{esc(subtitle)}</div>', sanitize=False)
        yield box


def label(text: str) -> None:
    ui.html(f'<div class="mx-label">{esc(text)}</div>', sanitize=False)


def metric(title: str, value: str, unit: str = "", hint: str = "", hot: bool = False) -> None:
    ui.html(
        f'<div class="mx-metric {"hot" if hot else ""}"><div class="mx-label">{esc(title)}</div>'
        f'<div class="v">{esc(value)}<span class="u">{esc(unit)}</span></div>'
        f'{f"<div class=h>{esc(hint)}</div>" if hint else ""}</div>', sanitize=False)


def notice(text: str, kind: str = "info", icon: str | None = None) -> None:
    icons = {"info": "info", "warn": "warning", "err": "error", "ok": "check_circle"}
    with ui.element("div").classes(f"mx-note {kind if kind != 'info' else ''}"):
        ui.icon(icon or icons.get(kind, "info")).classes("text-lg").style("margin-top:1px")
        ui.html(f"<div>{esc(text)}</div>", sanitize=False)


def formula_block(lines: list[str]) -> None:
    if lines:
        ui.html('<div class="mx-formula">' + "<br>".join(esc(line) for line in lines) + "</div>", sanitize=False).classes("w-full")


def chip(text: str, accent: bool = False) -> str:
    return f'<span class="mx-chip {"accent" if accent else ""}">{esc(text)}</span>'


def stacked_bar(items: list[tuple[str, float, str]]) -> None:
    """Horizontal stacked bar. items = (label, fraction 0..1, colour)."""
    items = [i for i in items if i[1] > 1e-6]
    segs = "".join(
        (f'<div style="width:{f * 100:.3f}%;background:{c}" title="{esc(n)}: {f * 100:.1f}%">{f * 100:.0f}%</div>' if f > 0.07
         else f'<div style="width:{f * 100:.3f}%;background:{c}" title="{esc(n)}: {f * 100:.1f}%"></div>')
        for n, f, c in items)
    legend = "".join(f'<span><i style="background:{c}"></i>{esc(n)} <b style="color:var(--ink)">{f * 100:.1f}%</b></span>' for n, f, c in items)
    ui.html(f'<div class="mx-bar">{segs}</div><div class="mx-legend">{legend}</div>', sanitize=False).classes("w-full")


def rating_scale(mm_per_year: float) -> None:
    """Six-step corrosion-resistance scale with a marker at the current rate (log scale)."""
    lo, hi = math.log10(0.005), math.log10(20.0)
    pos = (math.log10(max(mm_per_year, 1e-6)) - lo) / (hi - lo)
    pos = min(max(pos, 0.0), 1.0)
    bands = "".join(f'<div style="background:{c}"></div>' for _, _, c, _ in RATINGS)
    names = "".join(f"<span>{n}</span>" for _, n, _, _ in RATINGS)
    ui.html(f'<div style="padding-top:6px"><div class="mx-scale">{bands}<div class="mx-scale-marker" style="left:calc({pos * 100:.2f}% - 2px)"></div></div>'
            f'<div class="mx-scale-labels">{names}</div></div>', sanitize=False)


def table_html(headers: list[str], rows: list[list], num_cols: tuple[int, ...] = ()) -> None:
    head = "".join(f'<th class="{"num" if i in num_cols else ""}">{esc(h)}</th>' for i, h in enumerate(headers))
    body = "".join("<tr>" + "".join(f'<td class="{"num" if i in num_cols else ""}">{c}</td>' for i, c in enumerate(r)) + "</tr>" for r in rows)
    ui.html(f'<table class="mx-table"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>', sanitize=False).classes("w-full")


def fmt(value: float, digits: int = 4) -> str:
    """Compact number formatting that avoids long decimals."""
    if value == 0:
        return "0"
    if abs(value) >= 1e5 or abs(value) < 1e-3:
        return f"{value:.{max(digits - 1, 1)}e}"
    return f"{value:.{digits}g}"


def primary_button(text: str, on_click, icon: str | None = None):
    return ui.button(text, icon=icon, on_click=on_click, color=None).classes("mx-primary").props("no-caps unelevated")


def ghost_button(text: str, on_click, icon: str | None = None):
    return ui.button(text, icon=icon, on_click=on_click, color=None).classes("mx-ghost").props("no-caps flat")
