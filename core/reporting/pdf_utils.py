"""Small helpers shared by the PDF report builders (matplotlib PdfPages, A4 pages)."""
from __future__ import annotations

import textwrap

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

A4 = (8.27, 11.69)
INK, MUTED = "#1B2430", "#5B6B7A"


def new_page() -> Figure:
    fig = Figure(figsize=A4)
    FigureCanvasAgg(fig)
    return fig


def header(page: Figure, title: str, subtitle: str = "") -> float:
    """Title block; returns the y position (figure fraction) where content can start."""
    page.text(0.08, 0.955, title, fontsize=17, weight="bold", color=INK)
    if subtitle:
        page.text(0.08, 0.932, subtitle, fontsize=9, color=MUTED)
    page.add_artist(Line2D([0.08, 0.92], [0.92, 0.92], color="#C4C9CF", lw=0.8))
    return 0.90


def wrapped(page: Figure, x: float, y: float, text: str, width: int = 92, size: float = 9, color: str = INK,
            weight: str = "normal", line_gap: float = 0.0185) -> float:
    """Write wrapped text and return the y position below it."""
    for paragraph in text.split("\n"):
        for line in textwrap.wrap(paragraph, width) or [""]:
            page.text(x, y, line, fontsize=size, color=color, weight=weight, va="top")
            y -= line_gap * size / 9
    return y


def embed_figure(page: Figure, fig: Figure, rect: list[float]) -> None:
    """Rasterise ``fig`` into ``page`` at ``rect`` = [left, bottom, width, height]."""
    if fig.canvas is None or not hasattr(fig.canvas, "buffer_rgba"):
        FigureCanvasAgg(fig)
    fig.canvas.draw()
    img = np.asarray(fig.canvas.buffer_rgba())
    ax = page.add_axes(rect)
    ax.imshow(img)
    ax.axis("off")


def footer(page: Figure, text: str) -> None:
    page.text(0.08, 0.035, text, fontsize=7, color=MUTED, wrap=True)
