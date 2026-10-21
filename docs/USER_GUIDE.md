# User guide

Start the app with `python main.py` (or open the deployed link). The left menu has the three modules plus *Databases*, *History* and *Guide*. The sun/moon button switches light and dark mode.

## 1. Phase diagrams

1. Choose **Fe–Fe₃C**, **Cu–Ni** or **Pb–Sn**.
2. Set the **composition** (wt% of the second element) and the **temperature**: drag the sliders, type a number, press an **example chip**, or **click anywhere on the diagram**.
3. Read **2. Phases present**: the phase field, a stacked bar and a table with each phase's composition and amount.
4. **3. Lever rule, step by step** shows the tie-line and the arithmetic.
5. **4. Predicted microstructure** shows microconstituents (e.g. proeutectoid ferrite 56% + pearlite 44%), a schematic micrograph (press *New grain pattern* for another one) and a description.
6. *PDF report*, *Diagram PNG* and *Save to history* are under the results. The *Matplotlib view* tab shows the same diagram drawn with matplotlib.

*Worked check:* Cu–Ni, 35 wt% Ni, 1250 °C gives liquid 31.5 wt% Ni (68%) and α 42.5 wt% Ni (32%).
*Edge cases:* values outside the diagram show a red message; a point exactly on the eutectic / eutectoid / peritectic line is evaluated just below the line and explained.

## 2. Materials selection

1. **Constraints (left):** choose material classes and enter minimum and/or maximum for strength, modulus, density and cost. Empty = no limit. Presets set common limits.
2. **Design objective:** e.g. *Light, stiff beam* (M = E^½/ρ). Higher M is better.
3. The three cards show the best material, its index and how many candidates remain.
4. **Ashby chart:** red star = best, dashed line = constant M through it, grey = excluded. *Custom axes* plots any two properties.
5. **Ranked table:** click a row for details (specific stiffness, source, verified flag). *Download CSV*, *PDF report*, *Save to history*.

*Example from the project document:* press **Strength ≥ 200 MPa**, objective *Light, stiff beam*: the answer is CFRP (unidirectional) with 16 of 26 materials left.

## 3. Corrosion

**Step 1 – Corrosion rate.** Pick the method:
* *Weight loss*: initial/final mass, area, time (units selectable).
* *Corrosion current*: i_corr in µA/cm², mA/cm² or A/m².
* *Tafel extrapolation*: paste `potential (V), current density (A/cm²)` lines or press *Load example data*, set E_corr and the Tafel window (mV), then *Calculate*. The chart shows both fitted lines and their intersection.
* *Polarization resistance*: R_p, β_a, β_c (Stern–Geary).
The result gives mm/y, mpy and µm/y, a six-step relative-resistance scale, the working, and the years to lose a chosen thickness.

**Step 2 – Galvanic risk.** Choose the *Seawater* or *EMF* series, two metals, the cathode : anode area ratio and the environment. You get the risk level (Negligible → Severe), which metal corrodes, mitigation advice, the position in the series and an optional compatibility matrix for several metals.

**Step 3 – Protection plan.** Choose the metal, environment, service life, optionally the measured rate (button *Use rate from step 1*) and the galvanic couple. You get ranked recommendations (primary / supporting / consider) and, for steel in water or soil, **sacrificial-anode sizing** (current demand, charge, anode mass).

**Step 4 – Report.** Summarises what you have produced and downloads a PDF.

## 4. Databases

* **Materials:** add, edit, delete, toggle *verified*, reset to the original 26. Input is validated (e.g. density 1–25,000 kg/m³).
* **EMF and galvanic series:** add your own metals, edit or delete entries; reset to the original.
* **Corrosion materials:** density and equivalent weight of the built-in alloys.

## 5. History

Every *Save to history* is stored in SQLite. Click a row to see inputs and results; delete one or clear the list.

## Troubleshooting

| Problem | Fix |
|---|---|
| Red message instead of results | Read it: it names the field and the allowed range. |
| "No material meets every constraint" | Relax a limit or add a material class. |
| Tafel fit error | Widen the window or provide at least 3 points on each side of E_corr. |
| Edits vanish on the hosted site | Free hosting resets its disk on restart; keep permanent data in the JSON seed files. |
