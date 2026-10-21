"""Corrosion rate calculations (Theme 3): weight loss, i_corr, Tafel extrapolation, Stern–Geary.

Formulas (ASTM G1, G31, G102):
    weight loss   CR[mm/y] = 8.76·10⁴ · ΔW[g] / (A[cm²] · t[h] · ρ[g/cm³])
    electro-chem. CR[mm/y] = 3.27·10⁻³ · i_corr[µA/cm²] · EW / ρ          (Faraday's law)
    1 mm = 39.37 mil, so  CR[mpy] = 39.37 · CR[mm/y]
    Stern–Geary   i_corr = B / R_p ,  B = β_a β_c / (2.303 (β_a + β_c))
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from core.corrosion.materials import FARADAY
from core.exceptions import ValidationError

K_MM_PER_YEAR = 8.76e4
K1_MM = 3.27e-3
MM_TO_MIL = 39.3701
SECONDS_PER_YEAR = 3.15576e7

# (upper limit mm/y, rating, colour, meaning) — Fontana / Callister relative-resistance scale
RATINGS = [
    (0.02, "Outstanding", "#2FBF71", "Negligible attack. Suitable for critical parts such as pump shafts and valve seats."),
    (0.10, "Excellent", "#7BC96F", "Very low rate. Suitable where small metal loss can be tolerated."),
    (0.50, "Good", "#C8D655", "Acceptable for most service; inspect periodically."),
    (1.00, "Fair", "#F2C14E", "Noticeable loss. Acceptable only with a corrosion allowance or for short service."),
    (5.00, "Poor", "#EF8354", "High rate. Protection or a better material is normally needed."),
    (math.inf, "Unacceptable", "#E4572E", "Severe attack. Not suitable without major changes."),
]


def positive(value, name: str) -> float:
    if isinstance(value, bool):
        raise ValidationError(f"{name} must be a number.")
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{name} must be a number (got {value!r}).") from None
    if not math.isfinite(v) or v <= 0:
        raise ValidationError(f"{name} must be greater than zero (got {value!r}).")
    return v


def rate_rating(mm_per_year: float) -> tuple[str, str, str]:
    """(rating, colour, meaning) for a rate in mm/y."""
    for limit, name, color, text in RATINGS:
        if mm_per_year < limit:
            return name, color, text
    return RATINGS[-1][1:]  # pragma: no cover


@dataclass
class RateResult:
    method: str
    mm_per_year: float
    mpy: float
    um_per_year: float
    rating: str
    rating_color: str
    rating_text: str
    mass_loss_g_m2_year: float | None = None
    details: dict = field(default_factory=dict)
    formulas: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"method": self.method, "mm_per_year": self.mm_per_year, "mpy": self.mpy,
                "um_per_year": self.um_per_year, "rating": self.rating,
                "mass_loss_g_m2_year": self.mass_loss_g_m2_year, "details": self.details}


def _result(method: str, mm_y: float, formulas: list[str], details: dict, mass_loss: float | None = None) -> RateResult:
    rating, color, text = rate_rating(mm_y)
    return RateResult(method, mm_y, mm_y * MM_TO_MIL, mm_y * 1000.0, rating, color, text, mass_loss, details, formulas)


def weight_loss_rate(initial_mass_g: float, final_mass_g: float, area_cm2: float, hours: float,
                     density_g_cm3: float) -> RateResult:
    """Average uniform corrosion rate from coupon mass loss (ASTM G1 / G31)."""
    m0, m1 = positive(initial_mass_g, "Initial mass"), positive(final_mass_g, "Final mass")
    area, t, rho = positive(area_cm2, "Exposed area"), positive(hours, "Exposure time"), positive(density_g_cm3, "Density")
    if m1 >= m0:
        raise ValidationError("Final mass must be lower than initial mass (a mass gain means scale or deposits were not removed).")
    dw = m0 - m1
    mm_y = K_MM_PER_YEAR * dw / (area * t * rho)
    mass_loss = dw / (area * 1e-4) / (t / 8766.0)
    formulas = [f"ΔW = {m0:g} − {m1:g} = {dw:.5g} g",
                f"CR = 8.76×10⁴ · ΔW / (A · t · ρ) = 8.76×10⁴ · {dw:.5g} / ({area:g} · {t:g} · {rho:g}) = {mm_y:.4g} mm/y",
                f"CR(mpy) = {mm_y:.4g} × 39.37 = {mm_y * MM_TO_MIL:.4g} mpy"]
    return _result("Weight loss", mm_y, formulas, {"mass_loss_g": dw, "area_cm2": area, "hours": t, "density": rho}, mass_loss)


def electrochemical_rate(i_corr_uA_cm2: float, equivalent_weight: float, density_g_cm3: float, method: str = "Corrosion current") -> RateResult:
    """CR from corrosion current density via Faraday's law (ASTM G102)."""
    i, ew, rho = positive(i_corr_uA_cm2, "Corrosion current density"), positive(equivalent_weight, "Equivalent weight"), positive(density_g_cm3, "Density")
    mm_y = K1_MM * i * ew / rho
    mass_loss = i * 1e-6 * ew / FARADAY * SECONDS_PER_YEAR * 1e4
    formulas = [f"CR = 3.27×10⁻³ · i_corr · EW / ρ = 3.27×10⁻³ · {i:.4g} · {ew:.4g} / {rho:g} = {mm_y:.4g} mm/y",
                f"Faraday: mass loss rate = i · EW / F = {mass_loss:.4g} g/(m²·year)"]
    return _result(method, mm_y, formulas, {"i_corr_uA_cm2": i, "equivalent_weight": ew, "density": rho}, mass_loss)


@dataclass
class TafelFit:
    beta_a: float
    beta_c: float
    i_corr: float
    e_corr_fit: float
    r2_anodic: float
    r2_cathodic: float
    n_anodic: int
    n_cathodic: int
    a_anodic: float
    a_cathodic: float

    @property
    def i_corr_uA_cm2(self) -> float:
        return self.i_corr * 1e6


def _linfit(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    slope, intercept = np.polyfit(x, y, 1)
    pred = slope * x + intercept
    ss_res, ss_tot = float(np.sum((y - pred) ** 2)), float(np.sum((y - y.mean()) ** 2))
    return float(slope), float(intercept), (1.0 - ss_res / ss_tot) if ss_tot > 0 else 1.0


def tafel_extrapolation(potentials_v, currents_a_cm2, e_corr_v: float, window_v: tuple[float, float] = (0.05, 0.25)) -> TafelFit:
    """Fit the linear Tafel regions on both branches and intersect them.

    The branch is chosen by the sign of the overpotential η = E − E_corr. Only points
    with ``window[0] ≤ |η| ≤ window[1]`` are used.
    """
    e = np.asarray(potentials_v, dtype=float)
    i = np.abs(np.asarray(currents_a_cm2, dtype=float))
    if e.shape != i.shape or e.ndim != 1:
        raise ValidationError("Potential and current lists must have the same length.")
    if not np.all(np.isfinite(e)) or not np.all(np.isfinite(i)):
        raise ValidationError("Polarization data must be finite numbers.")
    lo, hi = window_v
    if not (0 <= lo < hi):
        raise ValidationError("Tafel window must satisfy 0 ≤ lower < upper (in volts).")
    eta = e - float(e_corr_v)
    valid = i > 0
    anodic = valid & (eta >= lo) & (eta <= hi)
    cathodic = valid & (eta <= -lo) & (eta >= -hi)
    if anodic.sum() < 3 or cathodic.sum() < 3:
        raise ValidationError(f"Need at least 3 points in each Tafel region (found {int(anodic.sum())} anodic, {int(cathodic.sum())} cathodic). "
                              "Widen the Tafel window or add data.")
    sa, a_a, r2a = _linfit(np.log10(i[anodic]), e[anodic])
    sc, a_c, r2c = _linfit(np.log10(i[cathodic]), e[cathodic])
    if sa <= 0:
        raise ValidationError("Anodic branch must have a positive Tafel slope (potential rising with current).")
    if sc >= 0:
        raise ValidationError("Cathodic branch must have a negative slope (potential falling as current rises).")
    beta_a, beta_c = sa, -sc
    log_i = (a_c - a_a) / (beta_a + beta_c)
    return TafelFit(beta_a, beta_c, 10 ** log_i, a_a + beta_a * log_i, r2a, r2c, int(anodic.sum()), int(cathodic.sum()), a_a, a_c)


def butler_volmer_data(i_corr: float, e_corr: float, beta_a: float, beta_c: float, eta_max: float = 0.35,
                       n: int = 71, noise: float = 0.0, seed: int = 1) -> tuple[np.ndarray, np.ndarray]:
    """Synthetic polarization curve (activation control) for demonstrations and tests."""
    for name, v in (("i_corr", i_corr), ("beta_a", beta_a), ("beta_c", beta_c), ("eta_max", eta_max)):
        positive(v, name)
    if n < 7:
        raise ValidationError("Need at least 7 points.")
    eta = np.linspace(-eta_max, eta_max, int(n))
    i = i_corr * (np.exp(2.302585 * eta / beta_a) - np.exp(-2.302585 * eta / beta_c))
    if noise > 0:
        i = i * (1 + np.random.default_rng(seed).normal(0, noise, i.shape))
    return e_corr + eta, i


def stern_geary(rp_ohm_cm2: float, beta_a: float, beta_c: float) -> tuple[float, float]:
    """(B in V, i_corr in A/cm²) from polarization resistance."""
    rp, ba, bc = positive(rp_ohm_cm2, "Polarization resistance"), positive(beta_a, "β_a"), positive(beta_c, "β_c")
    b = ba * bc / (2.303 * (ba + bc))
    return b, b / rp


def service_life(thickness_mm: float, rate_mm_per_year: float, allowable_loss_fraction: float = 1.0) -> float:
    """Years until ``allowable_loss_fraction`` of the thickness is lost at a constant rate."""
    t, r = positive(thickness_mm, "Thickness"), positive(rate_mm_per_year, "Corrosion rate")
    if not 0 < allowable_loss_fraction <= 1:
        raise ValidationError("Allowable loss fraction must be between 0 and 1.")
    return t * allowable_loss_fraction / r
