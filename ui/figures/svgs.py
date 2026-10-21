"""Inline SVG illustrations generated from real data (hero and theme cards)."""
from __future__ import annotations

import numpy as np

from core.phase.diagram import Equilibrium, PhaseDiagram, polygon_area


def diagram_svg(diagram: PhaseDiagram, eq: Equilibrium | None = None, width: int = 640, height: int = 400,
                labels: bool = True, pad: int = 34, axis_text: bool = True) -> str:
    """SVG of a phase diagram: coloured fields, invariant lines, optional alloy marker and tie-line."""
    (x0, x1), (t0, t1) = diagram.x_range, diagram.t_range

    def px(x): return pad + (x - x0) / (x1 - x0) * (width - 2 * pad)
    def py(t): return height - pad - (t - t0) / (t1 - t0) * (height - 2 * pad)

    out = [f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{diagram.title} phase diagram">']
    for r in diagram.regions:
        pts = " ".join(f"{px(x):.1f},{py(t):.1f}" for x, t in r.polygon)
        out.append(f'<polygon class="pf" points="{pts}" style="fill:{r.color}"><title>{r.name}</title></polygon>')
    for inv in diagram.invariants:
        out.append(f'<line x1="{px(inv.x_left):.1f}" x2="{px(inv.x_right):.1f}" y1="{py(inv.temperature):.1f}" y2="{py(inv.temperature):.1f}" '
                   f'stroke="var(--ink)" stroke-opacity=".7" stroke-dasharray="4 3" stroke-width="1"/>')
    if labels:
        min_area = 0.012 * diagram.bounding_area()
        for r in diagram.regions:
            if polygon_area(r.polygon) >= min_area:
                lx, ly = r.label_position
                out.append(f'<text x="{px(lx):.1f}" y="{py(ly):.1f}" text-anchor="middle" font-size="13" font-weight="700">{r.name}</text>')
    out.append(f'<rect x="{pad}" y="{pad}" width="{width - 2 * pad}" height="{height - 2 * pad}" fill="none" stroke="var(--ink)" stroke-opacity=".5"/>')
    if eq:
        if eq.tie_line:
            ty = py(eq.effective_temperature or eq.temperature)
            out.append(f'<line x1="{px(eq.tie_line[0]):.1f}" x2="{px(eq.tie_line[1]):.1f}" y1="{ty:.1f}" y2="{ty:.1f}" stroke="#F0647A" stroke-width="2.4"/>')
        out.append(f'<circle cx="{px(eq.x):.1f}" cy="{py(eq.temperature):.1f}" r="6.5" fill="#fff" stroke="#F0647A" stroke-width="3"/>')
    if axis_text:
        out.append(f'<text x="{width / 2}" y="{height - 8}" text-anchor="middle" font-size="12" fill-opacity=".7">{diagram.x_label}</text>')
        out.append(f'<text x="12" y="{height / 2}" text-anchor="middle" font-size="12" transform="rotate(-90 12 {height / 2})">Temperature (°C)</text>')
    out.append("</svg>")
    return "".join(out)


def ashby_svg(df, width: int = 300, height: int = 150) -> str:
    """Tiny log-log density-vs-modulus scatter coloured by material class."""
    from core.selection.properties import CLASS_COLORS
    lx, ly = np.log10(df["density"]), np.log10(df["modulus"])
    pad = 12

    def px(v): return pad + (v - lx.min()) / (lx.max() - lx.min()) * (width - 2 * pad)
    def py(v): return height - pad - (v - ly.min()) / (ly.max() - ly.min()) * (height - 2 * pad)

    out = [f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet">']
    for g in range(1, 5):
        out.append(f'<line x1="{pad}" x2="{width - pad}" y1="{height * g / 5:.0f}" y2="{height * g / 5:.0f}" stroke="var(--line)"/>')
    for _, r in df.iterrows():
        out.append(f'<circle cx="{px(np.log10(r["density"])):.1f}" cy="{py(np.log10(r["modulus"])):.1f}" r="4.2" fill="{CLASS_COLORS[r["material_class"]]}" fill-opacity=".9"/>')
    best = df.assign(m=np.sqrt(df["modulus"]) / df["density"]).sort_values("m").iloc[-1]
    bx, by = px(np.log10(best["density"])), py(np.log10(best["modulus"]))
    out.append(f'<line x1="{bx - 70:.1f}" y1="{by + 35:.1f}" x2="{bx + 40:.1f}" y2="{by - 20:.1f}" stroke="#F0647A" stroke-dasharray="4 3" stroke-width="1.4"/>')
    out.append(f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="7" fill="none" stroke="#F0647A" stroke-width="2"/></svg>')
    return "".join(out)


def ladder_svg(values: list[float], width: int = 300, height: int = 150) -> str:
    """Tiny potential ladder (bars from the most active to the most noble metal)."""
    vals = sorted(values)
    lo, hi = min(vals), max(vals)
    pad, n = 10, len(vals)
    bar_h = (height - 2 * pad) / n
    zero = pad + (0 - lo) / (hi - lo) * (width - 2 * pad)
    out = [f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none">']
    for i, v in enumerate(vals):
        x = pad + (v - lo) / (hi - lo) * (width - 2 * pad)
        color = "var(--verd)" if v < 0 else "#8EA0B8"
        out.append(f'<rect x="{min(x, zero):.1f}" y="{pad + i * bar_h:.1f}" width="{abs(x - zero):.1f}" height="{bar_h * 0.72:.1f}" rx="1.5" fill="{color}" fill-opacity=".85"/>')
    out.append(f'<line x1="{zero:.1f}" x2="{zero:.1f}" y1="{pad - 3}" y2="{height - pad + 3}" stroke="var(--ink)" stroke-opacity=".6"/></svg>')
    return "".join(out)
