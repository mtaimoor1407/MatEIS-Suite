"""Generate data/materials_seed.json from the table below.

Run:  python scripts/build_seed.py

Values are typical room-temperature figures compiled from standard references
(Callister & Rethwisch, *Materials Science and Engineering*, Appendix B;
MatWeb typical-property pages; Ashby, *Materials Selection in Mechanical Design*).
Cost is an indicative raw-material price in USD/kg and changes with the market.

IMPORTANT: every row ships with verified = false. Each team member must check
the row against the cited reference and then flip the flag (see
docs/DATA_VERIFICATION.md).
"""
import json
from pathlib import Path

CALLISTER = "Callister & Rethwisch, Materials Science and Engineering, App. B"
MATWEB = "MatWeb typical properties"
ASHBY = "Ashby, Materials Selection in Mechanical Design"

# name, class, density kg/m3, E GPa, strength MPa, basis, cost USD/kg, source, notes
ROWS = [
    # ---------------- Metals ----------------
    ("AISI 1020 Steel (hot rolled)", "Metal", 7870, 207, 350, "yield", 0.8, MATWEB, "Low-carbon plain steel; general structural use."),
    ("AISI 304 Stainless Steel (annealed)", "Metal", 8000, 193, 215, "yield", 3.5, CALLISTER, "Austenitic stainless; corrosion resistant."),
    ("AISI 4140 Steel (normalized)", "Metal", 7850, 205, 655, "yield", 1.5, MATWEB, "Cr-Mo alloy steel; shafts, gears."),
    ("Ductile Iron 65-45-12", "Metal", 7100, 169, 310, "yield", 1.0, CALLISTER, "Cast iron with spheroidal graphite."),
    ("Aluminum 6061-T6", "Metal", 2700, 69, 275, "yield", 3.0, CALLISTER, "Heat-treatable Al-Mg-Si alloy; very common."),
    ("Aluminum 7075-T6", "Metal", 2810, 72, 503, "yield", 4.5, MATWEB, "High-strength Al-Zn alloy; aerospace."),
    ("Titanium Ti-6Al-4V (annealed)", "Metal", 4430, 114, 880, "yield", 35.0, MATWEB, "Alpha-beta Ti alloy; aerospace and biomedical."),
    ("Copper C11000 (annealed)", "Metal", 8940, 110, 69, "yield", 9.0, CALLISTER, "Electrolytic tough-pitch copper."),
    ("Brass 70Cu-30Zn (annealed)", "Metal", 8530, 110, 75, "yield", 7.0, CALLISTER, "Cartridge brass."),
    ("Magnesium AZ31B (extruded)", "Metal", 1770, 45, 200, "yield", 4.5, CALLISTER, "Lightest structural metal family."),
    ("Inconel 718 (aged)", "Metal", 8190, 200, 1034, "yield", 40.0, MATWEB, "Nickel superalloy for high-temperature service."),
    # ---------------- Polymers ----------------
    ("HDPE", "Polymer", 960, 1.0, 26, "yield", 1.3, CALLISTER, "High-density polyethylene."),
    ("Polypropylene (PP)", "Polymer", 905, 1.5, 35, "yield", 1.4, CALLISTER, "Isotactic homopolymer."),
    ("Nylon 6,6 (dry)", "Polymer", 1140, 2.8, 55, "yield", 3.5, CALLISTER, "Strength drops when moisture is absorbed."),
    ("PMMA (acrylic)", "Polymer", 1190, 3.0, 70, "tensile", 2.5, CALLISTER, "Brittle: tensile strength used in place of yield."),
    ("PEEK", "Polymer", 1300, 3.6, 100, "yield", 90.0, MATWEB, "High-performance thermoplastic."),
    ("PVC (rigid)", "Polymer", 1400, 3.0, 45, "yield", 1.3, CALLISTER, "Unplasticized PVC."),
    ("Polycarbonate (PC)", "Polymer", 1200, 2.4, 62, "yield", 3.5, CALLISTER, "Tough, transparent thermoplastic."),
    # ---------------- Ceramics (flexural strength) ----------------
    ("Alumina Al2O3 (99.5%)", "Ceramic", 3890, 375, 380, "flexural", 15.0, CALLISTER, "Ceramics have no true yield point: flexural strength used."),
    ("Silicon Carbide (sintered)", "Ceramic", 3100, 410, 450, "flexural", 20.0, MATWEB, "Flexural strength used."),
    ("Silicon Nitride (hot pressed)", "Ceramic", 3300, 304, 700, "flexural", 50.0, CALLISTER, "Flexural strength used."),
    ("Zirconia Y-TZP", "Ceramic", 6050, 205, 900, "flexural", 40.0, CALLISTER, "Yttria-stabilised zirconia; flexural strength used."),
    ("Soda-Lime Glass", "Ceramic", 2500, 69, 69, "flexural", 1.0, CALLISTER, "Flexural strength used."),
    # ---------------- Composites ----------------
    ("CFRP unidirectional (0 deg)", "Composite", 1600, 135, 1500, "tensile", 60.0, ASHBY, "Along the fibre direction only; strongly anisotropic."),
    ("CFRP quasi-isotropic", "Composite", 1550, 60, 550, "tensile", 60.0, ASHBY, "Balanced lay-up; in-plane properties."),
    ("GFRP (E-glass / epoxy)", "Composite", 1900, 25, 350, "tensile", 6.0, ASHBY, "Woven E-glass in epoxy matrix."),
]

KEYS = ["name", "material_class", "density_kg_m3", "youngs_modulus_gpa",
        "yield_strength_mpa", "strength_basis", "cost_usd_per_kg", "source", "notes"]

if __name__ == "__main__":
    records = [dict(zip(KEYS, row, strict=True), verified=False) for row in ROWS]
    out = Path(__file__).resolve().parent.parent / "data" / "materials_seed.json"
    out.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(records)} materials to {out}")
