"""Draw a schematic micrograph for a Microstructure (PNG bytes, matplotlib + numpy).

The picture is a Voronoi mosaic of grains. Each grain is assigned to a
microconstituent so that the *area* fractions match the mass fractions closely,
and each constituent has its own texture (plain grains, lamellae, particles,
liquid). It is a teaching schematic, not a simulation.
"""
from __future__ import annotations

import io

import numpy as np
from matplotlib.colors import to_rgb
from matplotlib.image import imsave

from core.phase.microstructure import Microstructure


def _assign_grains(areas: np.ndarray, fractions: list[float], rng: np.random.Generator) -> np.ndarray:
    """Give each grain a constituent index so area shares track ``fractions``."""
    total = areas.sum()
    target = np.array(fractions, dtype=float) * total
    filled = np.zeros_like(target)
    out = np.zeros(len(areas), dtype=int)
    for g in rng.permutation(len(areas)):
        k = int(np.argmax(target - filled))
        out[g] = k
        filled[k] += areas[g]
    return out


def render_png(micro: Microstructure, width: int = 420, height: int = 280, seed: int = 7,
               n_grains: int = 46) -> bytes:
    rng = np.random.default_rng(seed)
    cons = [c for c in micro.constituents if c.fraction > 1e-9] or micro.constituents
    fracs = [c.fraction for c in cons]
    cols = int(round(np.sqrt(n_grains * width / height)))
    rows = int(np.ceil(n_grains / cols))
    gx, gy = np.meshgrid((np.arange(cols) + 0.5) / cols, (np.arange(rows) + 0.5) / rows)
    seeds = np.column_stack([gx.ravel() * width, gy.ravel() * height])
    seeds += rng.uniform(-0.38, 0.38, seeds.shape) * np.array([width / cols, height / rows])
    yy, xx = np.mgrid[0:height, 0:width]
    d2 = (xx[..., None] - seeds[:, 0]) ** 2 + (yy[..., None] - seeds[:, 1]) ** 2
    label = np.argmin(d2, axis=-1)
    areas = np.bincount(label.ravel(), minlength=len(seeds)).astype(float)
    kind = _assign_grains(areas, fracs, rng)
    img = np.zeros((height, width, 3))
    angle = rng.uniform(0, np.pi, len(seeds))
    period = rng.uniform(5.0, 7.5, len(seeds))
    shade = rng.uniform(-0.05, 0.05, len(seeds))
    noise = rng.random((height, width))
    for g in range(len(seeds)):
        c = cons[kind[g]]
        mask = label == g
        base = np.array(to_rgb(c.color))
        if c.texture == "lamellar":
            alt = np.array(to_rgb(c.color2 or "#FFFFFF"))
            phase = (xx[mask] * np.cos(angle[g]) + yy[mask] * np.sin(angle[g])) / period[g]
            stripe = (np.sin(2 * np.pi * phase) > 0).astype(float)[:, None]
            img[mask] = base * (1 - stripe) + alt * stripe
        elif c.texture == "matrix_particles":
            alt = np.array(to_rgb(c.color2 or "#000000"))
            blobs = (noise[mask] > 0.93).astype(float)[:, None]
            img[mask] = base * (1 - blobs) + alt * blobs
        elif c.texture == "liquid":
            img[mask] = np.clip(base + 0.06 * (noise[mask][:, None] - 0.5), 0, 1)
        else:
            img[mask] = np.clip(base + shade[g], 0, 1)
    edge = np.zeros((height, width), dtype=bool)
    edge[:, :-1] |= label[:, :-1] != label[:, 1:]
    edge[:-1, :] |= label[:-1, :] != label[1:, :]
    img[edge] = img[edge] * 0.35
    buf = io.BytesIO()
    imsave(buf, np.clip(img, 0, 1), format="png")
    return buf.getvalue()
