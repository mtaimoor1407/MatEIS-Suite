"""Input parsing helpers for the UI."""
from __future__ import annotations

import re

from core.exceptions import ValidationError


def parse_polarization(text: str) -> tuple[list[float], list[float]]:
    """Parse 'E, i' lines (comma, space, tab or semicolon separated). A text header line is skipped."""
    e_list, i_list = [], []
    for n, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p for p in re.split(r"[,\s;]+", line) if p]
        try:
            e, i = float(parts[0]), float(parts[1])
        except (ValueError, IndexError):
            if not e_list and n <= 2:
                continue  # header line
            raise ValidationError(f"Line {n} is not 'potential, current': {raw!r}") from None
        e_list.append(e)
        i_list.append(i)
    if len(e_list) < 7:
        raise ValidationError("Enter at least 7 data points (potential in V, current density in A/cm²).")
    return e_list, i_list
