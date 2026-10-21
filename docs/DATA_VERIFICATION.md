# Data verification sheet

**Why this matters:** 30% of the grade is *Materials Science Accuracy*. Every number in the app comes from a typical textbook figure. Before submission, each team member checks their share of the rows against the cited reference and signs the table.

**How to verify a row**

1. Open the cited reference (Callister Appendix B, MatWeb, Ashby, CRC Handbook).
2. Compare the numbers. Small differences are normal (grade, temper, test method).
3. If your reference differs by more than a few percent, edit `scripts/build_materials_seed.py` (materials) or `data/emf_series.json` (EMF), regenerate, and use *Databases → Reset to original*.
4. In the app open *Databases → Materials*, select the row, press *Toggle verified*.
5. Write the page or URL in *Checked against* and your name in *Verified by*.

## 1. Materials (Ashby tool)

| ✔ | Material | Class | ρ kg/m³ | E GPa | σ MPa (basis) | USD/kg | Cited source | Checked against | Verified by |
|---|---|---|---|---|---|---|---|---|---|
| ☐ | AISI 1020 Steel (hot rolled) | Metal | 7870 | 207 | 350 (yield) | 0.8 | MatWeb typical properties |  |  |
| ☐ | AISI 304 Stainless Steel (annealed) | Metal | 8000 | 193 | 215 (yield) | 3.5 | Callister & Rethwisch, Materials Science and Engineering, App. B |  |  |
| ☐ | AISI 4140 Steel (normalized) | Metal | 7850 | 205 | 655 (yield) | 1.5 | MatWeb typical properties |  |  |
| ☐ | Ductile Iron 65-45-12 | Metal | 7100 | 169 | 310 (yield) | 1 | Callister & Rethwisch, Materials Science and Engineering, App. B |  |  |
| ☐ | Aluminum 6061-T6 | Metal | 2700 | 69 | 275 (yield) | 3 | Callister & Rethwisch, Materials Science and Engineering, App. B |  |  |
| ☐ | Aluminum 7075-T6 | Metal | 2810 | 72 | 503 (yield) | 4.5 | MatWeb typical properties |  |  |
| ☐ | Titanium Ti-6Al-4V (annealed) | Metal | 4430 | 114 | 880 (yield) | 35 | MatWeb typical properties |  |  |
| ☐ | Copper C11000 (annealed) | Metal | 8940 | 110 | 69 (yield) | 9 | Callister & Rethwisch, Materials Science and Engineering, App. B |  |  |
| ☐ | Brass 70Cu-30Zn (annealed) | Metal | 8530 | 110 | 75 (yield) | 7 | Callister & Rethwisch, Materials Science and Engineering, App. B |  |  |
| ☐ | Magnesium AZ31B (extruded) | Metal | 1770 | 45 | 200 (yield) | 4.5 | Callister & Rethwisch, Materials Science and Engineering, App. B |  |  |
| ☐ | Inconel 718 (aged) | Metal | 8190 | 200 | 1034 (yield) | 40 | MatWeb typical properties |  |  |
| ☐ | HDPE | Polymer | 960 | 1 | 26 (yield) | 1.3 | Callister & Rethwisch, Materials Science and Engineering, App. B |  |  |
| ☐ | Polypropylene (PP) | Polymer | 905 | 1.5 | 35 (yield) | 1.4 | Callister & Rethwisch, Materials Science and Engineering, App. B |  |  |
| ☐ | Nylon 6,6 (dry) | Polymer | 1140 | 2.8 | 55 (yield) | 3.5 | Callister & Rethwisch, Materials Science and Engineering, App. B |  |  |
| ☐ | PMMA (acrylic) | Polymer | 1190 | 3 | 70 (tensile) | 2.5 | Callister & Rethwisch, Materials Science and Engineering, App. B |  |  |
| ☐ | PEEK | Polymer | 1300 | 3.6 | 100 (yield) | 90 | MatWeb typical properties |  |  |
| ☐ | PVC (rigid) | Polymer | 1400 | 3 | 45 (yield) | 1.3 | Callister & Rethwisch, Materials Science and Engineering, App. B |  |  |
| ☐ | Polycarbonate (PC) | Polymer | 1200 | 2.4 | 62 (yield) | 3.5 | Callister & Rethwisch, Materials Science and Engineering, App. B |  |  |
| ☐ | Alumina Al2O3 (99.5%) | Ceramic | 3890 | 375 | 380 (flexural) | 15 | Callister & Rethwisch, Materials Science and Engineering, App. B |  |  |
| ☐ | Silicon Carbide (sintered) | Ceramic | 3100 | 410 | 450 (flexural) | 20 | MatWeb typical properties |  |  |
| ☐ | Silicon Nitride (hot pressed) | Ceramic | 3300 | 304 | 700 (flexural) | 50 | Callister & Rethwisch, Materials Science and Engineering, App. B |  |  |
| ☐ | Zirconia Y-TZP | Ceramic | 6050 | 205 | 900 (flexural) | 40 | Callister & Rethwisch, Materials Science and Engineering, App. B |  |  |
| ☐ | Soda-Lime Glass | Ceramic | 2500 | 69 | 69 (flexural) | 1 | Callister & Rethwisch, Materials Science and Engineering, App. B |  |  |
| ☐ | CFRP unidirectional (0 deg) | Composite | 1600 | 135 | 1500 (tensile) | 60 | Ashby, Materials Selection in Mechanical Design |  |  |
| ☐ | CFRP quasi-isotropic | Composite | 1550 | 60 | 550 (tensile) | 60 | Ashby, Materials Selection in Mechanical Design |  |  |
| ☐ | GFRP (E-glass / epoxy) | Composite | 1900 | 25 | 350 (tensile) | 6 | Ashby, Materials Selection in Mechanical Design |  |  |

Costs are indicative raw-material prices, not quotes. Ceramics use flexural strength; some polymers and composites use tensile strength (no true yield point).

## 2. Phase diagrams (digitised, about ±10 °C and ±1 wt%)

The diagram boundaries are piece-wise linear approximations in `core/phase/diagrams.py`. Compare the key points below with the figure in your textbook.

| ✔ | Diagram | Feature | Value in the app | Textbook figure | Checked by |
|---|---|---|---|---|---|
| ☐ | Fe–Fe₃C | Eutectoid | 0.76 wt% C, 727 °C | Callister Fig. 9.24 |  |
| ☐ | Fe–Fe₃C | Eutectic | 4.30 wt% C, 1147 °C | Callister Fig. 9.24 |  |
| ☐ | Fe–Fe₃C | Max solubility in γ | 2.14 wt% C at 1147 °C | Callister Fig. 9.24 |  |
| ☐ | Fe–Fe₃C | Max solubility in α | 0.022 wt% C at 727 °C | Callister Fig. 9.24 |  |
| ☐ | Fe–Fe₃C | Peritectic | 0.09 / 0.17 / 0.53 wt% C at 1493 °C | Callister Fig. 9.24 |  |
| ☐ | Fe–Fe₃C | Cementite | 6.70 wt% C | Callister Fig. 9.24 |  |
| ☐ | Cu–Ni | Melting points | Cu 1085 °C, Ni 1455 °C | Callister Fig. 9.3a |  |
| ☐ | Cu–Ni | Worked example | 35 wt% Ni, 1250 °C → C_L 31.5, C_α 42.5, W_α 0.32 | Callister Example 9.1/9.2 |  |
| ☐ | Pb–Sn | Eutectic | 61.9 wt% Sn, 183 °C | Callister Fig. 9.8 |  |
| ☐ | Pb–Sn | Eutectic phase limits | α 18.3, β 97.8 wt% Sn | Callister Fig. 9.8 |  |
| ☐ | Pb–Sn | Worked example | 40 wt% Sn, 150 °C → C_α 11, C_β 99, W_α 0.67 | Callister Example 9.2 |  |

## 3. EMF series (V vs SHE)

| ✔ | Metal | Potential (V) | Source | Checked by |
|---|---|---|---|---|
| ☐ | Sodium | -2.714 | Callister Table 17.1 |  |
| ☐ | Magnesium | -2.363 | Callister Table 17.1 |  |
| ☐ | Aluminum | -1.662 | Callister Table 17.1 |  |
| ☐ | Titanium | -1.630 | CRC Handbook |  |
| ☐ | Manganese | -1.185 | CRC Handbook |  |
| ☐ | Zinc | -0.763 | Callister Table 17.1 |  |
| ☐ | Chromium | -0.744 | Callister Table 17.1 |  |
| ☐ | Iron | -0.440 | Callister Table 17.1 |  |
| ☐ | Cadmium | -0.403 | Callister Table 17.1 |  |
| ☐ | Cobalt | -0.277 | Callister Table 17.1 |  |
| ☐ | Nickel | -0.250 | Callister Table 17.1 |  |
| ☐ | Tin | -0.136 | Callister Table 17.1 |  |
| ☐ | Lead | -0.126 | Callister Table 17.1 |  |
| ☐ | Hydrogen (reference) | +0.000 | Definition of SHE |  |
| ☐ | Copper | +0.340 | Callister Table 17.1 |  |
| ☐ | Silver | +0.800 | Callister Table 17.1 |  |
| ☐ | Palladium | +0.951 | CRC Handbook |  |
| ☐ | Platinum | +1.200 | CRC / Callister |  |
| ☐ | Gold | +1.420 | Callister Table 17.1 |  |

## 4. Galvanic series in seawater (V vs SCE, typical mid-range)

| ✔ | Metal | Potential (V) | Source | Checked by |
|---|---|---|---|---|
| ☐ | Magnesium alloys | -1.600 | Typical mid-range of ASTM G82-type galvanic series in flowing seawater (order follows Fontana) |  |
| ☐ | Zinc | -1.030 | Typical mid-range of ASTM G82-type galvanic series in flowing seawater (order follows Fontana) |  |
| ☐ | Aluminum (1100 / 5052 / 6061) | -0.800 | Typical mid-range of ASTM G82-type galvanic series in flowing seawater (order follows Fontana) |  |
| ☐ | Cadmium | -0.730 | Typical mid-range of ASTM G82-type galvanic series in flowing seawater (order follows Fontana) |  |
| ☐ | Aluminum 2024 | -0.690 | Typical mid-range of ASTM G82-type galvanic series in flowing seawater (order follows Fontana) |  |
| ☐ | Carbon / mild steel | -0.650 | Typical mid-range of ASTM G82-type galvanic series in flowing seawater (order follows Fontana) |  |
| ☐ | Cast iron | -0.620 | Typical mid-range of ASTM G82-type galvanic series in flowing seawater (order follows Fontana) |  |
| ☐ | Stainless steel 304 (active) | -0.520 | Typical mid-range of ASTM G82-type galvanic series in flowing seawater (order follows Fontana) |  |
| ☐ | Lead | -0.500 | Typical mid-range of ASTM G82-type galvanic series in flowing seawater (order follows Fontana) |  |
| ☐ | Tin | -0.420 | Typical mid-range of ASTM G82-type galvanic series in flowing seawater (order follows Fontana) |  |
| ☐ | Brass (admiralty) | -0.360 | Typical mid-range of ASTM G82-type galvanic series in flowing seawater (order follows Fontana) |  |
| ☐ | Copper | -0.340 | Typical mid-range of ASTM G82-type galvanic series in flowing seawater (order follows Fontana) |  |
| ☐ | Bronze | -0.310 | Typical mid-range of ASTM G82-type galvanic series in flowing seawater (order follows Fontana) |  |
| ☐ | Copper–nickel 70/30 | -0.250 | Typical mid-range of ASTM G82-type galvanic series in flowing seawater (order follows Fontana) |  |
| ☐ | Monel 400 | -0.140 | Typical mid-range of ASTM G82-type galvanic series in flowing seawater (order follows Fontana) |  |
| ☐ | Nickel 200 (passive) | -0.100 | Typical mid-range of ASTM G82-type galvanic series in flowing seawater (order follows Fontana) |  |
| ☐ | Stainless steel 304 (passive) | -0.080 | Typical mid-range of ASTM G82-type galvanic series in flowing seawater (order follows Fontana) |  |
| ☐ | Stainless steel 316 (passive) | -0.050 | Typical mid-range of ASTM G82-type galvanic series in flowing seawater (order follows Fontana) |  |
| ☐ | Silver | -0.030 | Typical mid-range of ASTM G82-type galvanic series in flowing seawater (order follows Fontana) |  |
| ☐ | Titanium (commercially pure) | +0.000 | Typical mid-range of ASTM G82-type galvanic series in flowing seawater (order follows Fontana) |  |
| ☐ | Graphite | +0.180 | Typical mid-range of ASTM G82-type galvanic series in flowing seawater (order follows Fontana) |  |
| ☐ | Gold | +0.200 | Typical mid-range of ASTM G82-type galvanic series in flowing seawater (order follows Fontana) |  |
| ☐ | Platinum | +0.250 | Typical mid-range of ASTM G82-type galvanic series in flowing seawater (order follows Fontana) |  |

The seawater series order follows Fontana's galvanic series; the numeric values are typical mid-range figures and scatter by ±0.05–0.15 V in practice. State this in your presentation.

## 5. Corrosion constants

| Constant | Value | Source |
|---|---|---|
| Weight-loss constant | 8.76×10⁴ (mm/y; g, cm², h, g/cm³) | ASTM G1 / G31 |
| i_corr constant | 3.27×10⁻³ mm·g/(µA·cm·y) | ASTM G102 |
| Equivalent weights | Fe 27.92, Al 8.99, Cu 31.77, Zn 32.69, 304 SS 25.12 | ASTM G102 |
| Relative resistance scale | <0.02 / 0.1 / 0.5 / 1 / 5 mm/y | Fontana; Callister Table 17.3 |
| Zinc corrosion rates in air | C2 0.1–0.7, C3–C4 0.7–4.2, C5 4.2–8.4 µm/y | ISO 9224 |
