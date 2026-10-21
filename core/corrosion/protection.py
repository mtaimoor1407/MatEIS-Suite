"""Corrosion protection recommendations and sacrificial-anode sizing (Theme 3).

The planner is a transparent rule base: every recommendation says *why* it was made.
It is a screening aid for students and early design, not a replacement for a
corrosion specification (ISO 12944, NACE SP0169, DNV-RP-B401).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from core.corrosion.materials import CorrosionMaterial
from core.exceptions import ValidationError


@dataclass(frozen=True)
class Environment:
    key: str
    label: str
    iso: str
    zinc_rate_um_year: tuple[float, float] | None
    immersed: bool
    default_current_density: float | None = None    # mA/m² bare steel, for cathodic protection


ENVIRONMENTS: dict[str, Environment] = {e.label: e for e in [
    Environment("indoor", "Indoor dry atmosphere", "C1", (0.0, 0.1), False),
    Environment("rural", "Rural atmosphere", "C2", (0.1, 0.7), False),
    Environment("urban", "Urban / industrial atmosphere", "C3–C4", (0.7, 4.2), False),
    Environment("marine_air", "Marine atmosphere (coastal)", "C5 (C5-M)", (4.2, 8.4), False),
    Environment("seawater", "Seawater immersion", "Im2", None, True, 100.0),
    Environment("freshwater", "Freshwater immersion", "Im1", None, True, 30.0),
    Environment("soil", "Buried in soil", "Im3", None, True, 20.0),
    Environment("chemical", "Acidic / chemical process", "—", None, False),
]}


def get_environment(label: str) -> Environment:
    try:
        return ENVIRONMENTS[label]
    except KeyError:
        raise ValidationError(f"Unknown environment '{label}'.") from None


@dataclass(frozen=True)
class AnodeMaterial:
    key: str
    name: str
    potential: str
    capacity_ah_per_kg: float
    typical_use: str
    environments: tuple[str, ...]


ANODES: dict[str, AnodeMaterial] = {a.key: a for a in [
    AnodeMaterial("zinc", "Zinc (ASTM B418 Type I/II)", "−1.05 V vs Ag/AgCl", 780.0,
                  "Seawater and brackish water, ship hulls, offshore jackets (below about 50 °C).", ("seawater", "freshwater")),
    AnodeMaterial("aluminum", "Aluminium–zinc–indium", "−1.05 V vs Ag/AgCl", 2500.0,
                  "Offshore structures and pipelines in seawater: light, high capacity.", ("seawater",)),
    AnodeMaterial("magnesium", "Magnesium (AZ63 / H-1 alloy)", "−1.55 V vs Cu/CuSO₄", 1100.0,
                  "Soil and freshwater: highest driving voltage, works in high-resistivity electrolytes.", ("soil", "freshwater")),
]}


def recommended_anode(substrate: CorrosionMaterial, env: Environment) -> AnodeMaterial | None:
    if substrate.family not in ("steel", "aluminum", "copper", "stainless"):
        return None
    if env.key == "seawater":
        return ANODES["aluminum"] if substrate.family == "steel" else ANODES["zinc"]
    if env.key in ("freshwater", "soil"):
        return ANODES["magnesium"]
    return None


@dataclass
class AnodeDesign:
    anode: AnodeMaterial
    area_m2: float
    current_density_ma_m2: float
    breakdown_factor: float
    life_years: float
    utilization: float
    current_a: float
    charge_ah: float
    mass_kg: float
    formulas: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"anode": self.anode.name, "area_m2": self.area_m2, "current_density_ma_m2": self.current_density_ma_m2,
                "breakdown_factor": self.breakdown_factor, "life_years": self.life_years,
                "current_a": self.current_a, "mass_kg": self.mass_kg}


def _pos(v, name: str) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0:
        raise ValidationError(f"{name} must be a number greater than zero.")
    return float(v)


def size_anodes(anode: AnodeMaterial, area_m2: float, current_density_ma_m2: float, life_years: float,
                breakdown_factor: float = 1.0, utilization: float = 0.85) -> AnodeDesign:
    """Total anode mass for a cathodic-protection design (mass-based, ignores resistance check)."""
    area, i_d, life = _pos(area_m2, "Surface area"), _pos(current_density_ma_m2, "Current density"), _pos(life_years, "Design life")
    if not 0 < breakdown_factor <= 1:
        raise ValidationError("Coating breakdown factor must be between 0 and 1 (1 = bare metal).")
    if not 0.3 <= utilization <= 1:
        raise ValidationError("Utilisation factor must be between 0.3 and 1.")
    current = area * breakdown_factor * i_d / 1000.0
    charge = current * life * 8766.0
    mass = charge / (anode.capacity_ah_per_kg * utilization)
    formulas = [f"I = A · f · i = {area:g} m² · {breakdown_factor:g} · {i_d:g} mA/m² = {current:.4g} A",
                f"Charge = I · t = {current:.4g} A · {life:g} y · 8766 h/y = {charge:,.0f} A·h",
                f"Mass = Charge / (capacity · u) = {charge:,.0f} / ({anode.capacity_ah_per_kg:g} · {utilization:g}) = {mass:,.1f} kg"]
    return AnodeDesign(anode, area, i_d, breakdown_factor, life, utilization, current, charge, mass, formulas)


@dataclass
class Recommendation:
    category: str
    title: str
    priority: int          # 1 = primary, 2 = supporting, 3 = consider
    why: str
    details: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"category": self.category, "title": self.title, "priority": self.priority, "why": self.why, "details": self.details}


def _coating_steel(env: Environment) -> list[Recommendation]:
    z = env.zinc_rate_um_year
    if env.key == "indoor":
        return [Recommendation("Coating", "Single-coat alkyd or epoxy primer (40–80 µm)", 1,
                               "Indoor dry air is a very mild category (C1); a thin barrier coat or even bare steel is normally adequate.",
                               ["Clean to Sa 2 (blast) or St 2 (hand/power tool) before coating."])]
    recs = []
    if env.key == "rural":
        recs.append(Recommendation("Coating", "Alkyd or acrylic paint system (80–120 µm total) on blasted steel", 1,
                                   "Low-corrosivity (C2) air needs a moderate barrier film.", ["Blast to Sa 2½ for best adhesion."]))
    elif env.key == "urban":
        recs.append(Recommendation("Coating", "Zinc-rich epoxy primer (60–80 µm) + epoxy build coat + polyurethane topcoat (≈200–240 µm)", 1,
                                   "C3–C4 air contains SO₂ and particulates; a three-coat system gives barrier plus sacrificial zinc protection.",
                                   ["Blast to Sa 2½.", "Typical ISO 12944-5 system for medium to high durability."]))
    elif env.key == "marine_air":
        recs.append(Recommendation("Coating", "Zinc-rich epoxy primer (60–80 µm) + epoxy MIO (160 µm) + polyurethane topcoat (60 µm), ≈280–320 µm total", 1,
                                   "Chloride-laden air (C5-M) is the harshest atmospheric category; a thick multi-coat system is standard practice.",
                                   ["Blast to Sa 2½.", "Specify stripe coats on edges, welds and bolts."]))
    if z:
        lo_life = 85.0 / z[1]
        hi_text = ">100" if z[0] <= 0 else f"{85.0 / z[0]:.0f}"
        recs.append(Recommendation("Coating", "Hot-dip galvanizing, ≥85 µm (ASTM A123), optionally duplex (zinc + paint)", 2,
                                   f"Zinc corrodes slowly in {env.iso} air (ISO 9224: {z[0]:g}–{z[1]:g} µm/y), and protects steel sacrificially at scratches.",
                                   [f"Estimated zinc coating life ≈ {lo_life:.0f}–{hi_text} years to first maintenance (85 µm ÷ corrosion rate).",
                                    "Estimate only: it assumes steady rates and an intact coating."]))
    return recs


def recommend(substrate: CorrosionMaterial, env: Environment, service_life_years: float = 20.0,
              current_rate_mm_year: float | None = None, galvanic_partner: str | None = None,
              galvanic_level: str | None = None) -> list[Recommendation]:
    """Ranked protection options for a substrate in an environment."""
    life = _pos(service_life_years, "Service life")
    recs: list[Recommendation] = []
    fam = substrate.family

    if fam == "steel":
        if env.key in ("indoor", "rural", "urban", "marine_air"):
            recs += _coating_steel(env)
            if env.key == "marine_air":
                recs.append(Recommendation("Material", "Avoid weathering (Cor-Ten) steel near the coast", 3,
                                           "Chlorides prevent the protective rust patina from forming."))
        elif env.key == "seawater":
            recs.append(Recommendation("Coating", "Two-coat epoxy system, 300–500 µm dry film (or glass-flake epoxy in the splash zone)", 1,
                                       "Bare steel loses roughly 0.1 mm/y in seawater; a thick barrier coat slows this and cuts the cathodic-protection current demand by 90% or more."))
            recs.append(Recommendation("Cathodic protection", "Sacrificial anodes: aluminium–zinc–indium (or zinc)", 1,
                                       "Immersed steel can be held at about −0.80 V vs Ag/AgCl by a more active metal. Al–Zn–In has the highest capacity per kg.",
                                       ["Size the anodes with the calculator below.", "Use impressed-current (ICCP) for very large or long-life structures."]))
        elif env.key == "freshwater":
            recs.append(Recommendation("Coating", "Epoxy or polyurethane lining, 250–400 µm", 1, "Barrier coat reduces the area needing cathodic protection."))
            recs.append(Recommendation("Cathodic protection", "Magnesium sacrificial anodes", 2,
                                       "Freshwater has high resistivity, so the high driving voltage of magnesium is needed."))
        elif env.key == "soil":
            recs.append(Recommendation("Coating", "Fusion-bonded epoxy (FBE) or three-layer polyethylene (3LPE) for pipes", 1,
                                       "A high-integrity coating is the primary barrier on buried steel."))
            recs.append(Recommendation("Cathodic protection", "Magnesium anodes in backfill (or impressed current for long pipelines)", 1,
                                       "Protective criterion: −0.85 V vs Cu/CuSO₄ (NACE SP0169).", ["Soil resistivity and pH decide the anode spacing."]))
        elif env.key == "chemical":
            recs.append(Recommendation("Material", "Change to stainless steel 316, duplex stainless or a nickel alloy; or line the vessel (glass-flake epoxy, rubber, PTFE)", 1,
                                       "Carbon steel corrodes quickly in acids; coatings alone rarely last in chemical service."))
            recs.append(Recommendation("Inhibitor", "Add a film-forming or anodic corrosion inhibitor suited to the fluid", 2,
                                       "Inhibitors are effective in closed or recirculating systems.", ["Test the inhibitor with weight-loss coupons first."]))
    elif fam == "stainless":
        recs.append(Recommendation("Surface treatment", "Pickle and passivate (nitric or citric acid, ASTM A967)", 1,
                                   "Removes free iron and weld heat tint so the chromium oxide film can form."))
        if env.key in ("seawater", "marine_air", "chemical"):
            recs.append(Recommendation("Material", "Upgrade 304 → 316 → duplex 2205 → super-austenitic (6Mo) as chloride level rises", 1,
                                       "Chloride pitting and crevice corrosion is the main risk. Pitting resistance PREN ≈ 18 (304), 24 (316), 35 (2205), 43 (6Mo).",
                                       ["Avoid crevices and stagnant water."]))
        else:
            recs.append(Recommendation("Design", "Keep surfaces clean and free-draining", 2, "Deposits create crevices where the passive film breaks down."))
    elif fam == "aluminum":
        recs.append(Recommendation("Surface treatment", "Anodize (Type II, 10–25 µm; Type III hard coat for wear) and seal", 1,
                                   "A thick, sealed oxide layer greatly improves resistance in air."))
        if env.key in ("seawater", "marine_air"):
            recs.append(Recommendation("Material", "Use marine-grade 5xxx or 6xxx alloys; avoid copper-bearing 2xxx and 7xxx alloys", 1,
                                       "Copper-rich alloys are prone to pitting and exfoliation in chloride environments."))
            recs.append(Recommendation("Coating", "Chromate-free conversion coat + epoxy primer + polyurethane topcoat", 2, "Barrier protection over the oxide film."))
        if env.key == "soil":
            recs.append(Recommendation("Design", "Check soil pH: aluminium corrodes below pH 4.5 and above pH 9", 1, "Amphoteric oxide dissolves in strong acid and alkali."))
    elif fam == "copper":
        if env.key in ("seawater", "marine_air"):
            recs.append(Recommendation("Material", "Use copper–nickel 90/10 or 70/30, or inhibited (arsenical) brass for seawater", 1,
                                       "Plain brass suffers dezincification in seawater."))
            recs.append(Recommendation("Cathodic protection", "Sacrificial iron or zinc anodes", 2, "Iron anodes keep copper surfaces from fouling by copper ions."))
        else:
            recs.append(Recommendation("Coating", "Clear lacquer or benzotriazole (BTA) treatment", 1, "Prevents tarnish and green patina."))
    elif fam == "zinc":
        z = env.zinc_rate_um_year
        if z:
            recs.append(Recommendation("Coating", "Duplex system: paint over galvanizing", 1,
                                       f"Bare zinc loses {z[0]:g}–{z[1]:g} µm/y in {env.iso} air; paint extends life by about 1.5–2.5 times.",
                                       ["Use a primer approved for galvanized surfaces."]))
        else:
            recs.append(Recommendation("Material", "Zinc is unsuitable in strong acids/alkalis; choose a more resistant alloy", 1, "Zinc dissolves rapidly outside pH 6–12."))
    elif fam == "magnesium":
        recs.append(Recommendation("Surface treatment", "Conversion coating or plasma electrolytic oxidation + sealed paint system", 1,
                                   "Magnesium is the most active structural metal; bare surfaces corrode rapidly in damp or salty conditions."))
        recs.append(Recommendation("Design", "Isolate completely from other metals and from wet insulation", 1, "Any contact with a nobler metal causes severe galvanic attack."))
    elif fam in ("titanium", "nickel"):
        recs.append(Recommendation("Material", f"{substrate.name} is already highly resistant here; no coating needed", 1,
                                   "Passive oxide film (TiO₂ or Cr₂O₃) protects in most natural environments.",
                                   ["Watch for crevices and for contact with much more active metals (hydrogen embrittlement of Ti with cathodic protection)."]))
    else:
        recs.append(Recommendation("Coating", "Apply a barrier coating suited to the environment", 2, "General rule for metals with limited natural resistance."))

    if current_rate_mm_year and current_rate_mm_year > 0:
        allowance = current_rate_mm_year * life
        recs.append(Recommendation("Design", f"Add a corrosion allowance of about {allowance:.2f} mm per exposed face", 2,
                                   f"Measured rate {current_rate_mm_year:.3g} mm/y × {life:g} years of service. Use it only if the protection above is not applied.",
                                   ["Round up and add a margin for localized (pitting) attack."]))
    if galvanic_partner and galvanic_level in ("Moderate", "High", "Severe"):
        recs.append(Recommendation("Design", f"Break the galvanic couple with {galvanic_partner}", 1,
                                   f"The galvanic assessment rated this couple '{galvanic_level}'.",
                                   ["Insulating washers or sleeves, coat the nobler metal, keep the anode large."]))
    recs.append(Recommendation("Design", "Design out crevices; ensure drainage and avoid water traps", 3, "Stagnant water and crevices start most localized corrosion."))
    recs.append(Recommendation("Maintenance", "Inspect on a schedule and keep records (visual, thickness, coupon or potential survey)", 3,
                               f"For a {life:g}-year life, plan periodic coating repair and anode-consumption checks."))
    recs.sort(key=lambda r: r.priority)
    return recs
