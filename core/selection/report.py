"""CSV and PDF exports. The PDF uses matplotlib (static Ashby chart + table)."""
from __future__ import annotations

import io
from datetime import datetime

import numpy as np
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure

from core.selection.filters import Constraints
from core.selection.indices import PerformanceIndex, guide_line
from core.selection.properties import CLASS_COLORS, EXCLUDED_COLOR, MATERIAL_CLASSES, WINNER_COLOR, axis_label

EXPORT_COLUMNS = ["rank", "name", "material_class", "density", "modulus", "strength",
                  "strength_basis", "cost", "cost_vol", "index_value", "source", "verified"]


def csv_bytes(ranked: pd.DataFrame) -> bytes:
    """Ranked results as UTF-8 CSV (with BOM so Excel shows symbols correctly)."""
    cols = [c for c in EXPORT_COLUMNS if c in ranked.columns]
    return ranked[cols].to_csv(index=False).encode("utf-8-sig")


def static_ashby_figure(all_df: pd.DataFrame, ranked: pd.DataFrame, index: PerformanceIndex,
                        x_key: str | None = None, y_key: str | None = None) -> Figure:
    """Matplotlib Ashby chart: classes coloured, excluded materials grey, winner starred."""
    x_key, y_key = (x_key or index.axes[0]), (y_key or index.axes[1])
    fig = Figure(figsize=(9, 6.2), dpi=110)
    FigureCanvasAgg(fig)  # attach an Agg canvas so the figure can be rasterised
    ax = fig.subplots()
    passing = set(ranked["name"]) if not ranked.empty else set()
    excluded = all_df[~all_df["name"].isin(passing)]
    if not excluded.empty:
        ax.scatter(excluded[x_key], excluded[y_key], s=34, c=EXCLUDED_COLOR, label="Excluded by constraints", zorder=2)
    for cls in MATERIAL_CLASSES:
        sub = ranked[ranked["material_class"] == cls] if not ranked.empty else ranked
        if len(sub):
            ax.scatter(sub[x_key], sub[y_key], s=52, c=CLASS_COLORS[cls], label=cls, zorder=3, edgecolors="white", linewidths=0.6)
    if not ranked.empty:
        best = ranked.iloc[0]
        if (x_key, y_key) == index.axes:
            x_lo, x_hi = all_df[x_key].min() / 1.6, all_df[x_key].max() * 1.6
            gx, gy = guide_line(index, best[x_key], best[y_key], x_lo, x_hi)
            ax.plot(gx, gy, "--", color=WINNER_COLOR, lw=1.2, label=f"Guide line: {index.formula} = {best['index_value']:.3g}", zorder=1)
        ax.scatter([best[x_key]], [best[y_key]], s=220, marker="*", c=WINNER_COLOR, zorder=4, label=f"Best: {best['name']}")
        for _, row in ranked.head(5).iterrows():
            ax.annotate(row["name"], (row[x_key], row[y_key]), xytext=(5, 5), textcoords="offset points", fontsize=7)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(axis_label(x_key))
    ax.set_ylabel(axis_label(y_key))
    ax.set_ylim(all_df[y_key].min() / 1.6, all_df[y_key].max() * 1.6)
    ax.set_xlim(all_df[x_key].min() / 1.6, all_df[x_key].max() * 1.6)
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(fontsize=7, loc="best")
    ax.set_title(f"Ashby chart – {index.label}", fontsize=11)
    fig.tight_layout()
    return fig


def pdf_report(all_df: pd.DataFrame, ranked: pd.DataFrame, index: PerformanceIndex,
               constraints: Constraints, top_n: int = 12) -> bytes:
    """Two-page PDF: summary + chart, then the ranked table."""
    buffer = io.BytesIO()
    with PdfPages(buffer) as pdf:
        # ---- page 1: summary and chart ----
        page = Figure(figsize=(8.27, 11.69))  # A4 portrait
        page.text(0.08, 0.95, "MatEIS Select – Material Selection Report", fontsize=17, weight="bold")
        page.text(0.08, 0.925, f"Generated {datetime.now():%Y-%m-%d %H:%M}", fontsize=9, color="#555")
        lines = [f"Objective: {index.label}",
                 f"Performance index: M = {index.formula}  [{index.unit}]",
                 f"Candidates after filtering: {len(ranked)} of {len(all_df)}", "", "Constraints:"]
        lines += [f"  • {c}" for c in constraints.describe()]
        if not ranked.empty:
            best = ranked.iloc[0]
            lines += ["", f"Recommended material: {best['name']}  (M = {best['index_value']:.3g})"]
        else:
            lines += ["", "No material satisfies every constraint."]
        page.text(0.08, 0.88, "\n".join(lines), fontsize=10, va="top", linespacing=1.5)
        chart = static_ashby_figure(all_df, ranked, index)
        chart.canvas.draw()
        img = np.asarray(chart.canvas.buffer_rgba())
        ax = page.add_axes([0.06, 0.07, 0.88, 0.50])
        ax.imshow(img)
        ax.axis("off")
        pdf.savefig(page)
        # ---- page 2: ranked table ----
        page2 = Figure(figsize=(8.27, 11.69))
        page2.text(0.08, 0.95, f"Top {min(top_n, len(ranked))} ranked materials", fontsize=14, weight="bold")
        if ranked.empty:
            page2.text(0.08, 0.90, "Nothing to rank. Relax one or more constraints.", fontsize=10)
        else:
            top = ranked.head(top_n)
            cells = [[int(r["rank"]), r["name"], r["material_class"], f"{r['density']:.2f}",
                      f"{r['modulus']:.3g}", f"{r['strength']:.4g}", f"{r['cost']:.3g}", f"{r['index_value']:.3g}"]
                     for _, r in top.iterrows()]
            header = ["#", "Material", "Class", "ρ\nMg/m³", "E\nGPa", "σ\nMPa", "Cost\nUSD/kg", "M"]
            ax2 = page2.add_axes([0.05, 0.45, 0.9, 0.45])
            ax2.axis("off")
            table = ax2.table(cellText=cells, colLabels=header, loc="upper center", cellLoc="left",
                              colWidths=[0.05, 0.32, 0.12, 0.09, 0.09, 0.09, 0.1, 0.1])
            table.auto_set_font_size(False)
            table.set_fontsize(8)
            table.scale(1, 1.6)
        page2.text(0.08, 0.06,
                   "Data are typical textbook values (see data/materials_seed.json for sources). "
                   "Ceramic strength is flexural strength; verify before final design.",
                   fontsize=7, color="#555", wrap=True)
        pdf.savefig(page2)
    return buffer.getvalue()
