# Presentation outline (10–12 minutes, 11 slides)

1. **Title:** MatEIS, team names and registration numbers, sessions, instructor.
2. **Problem:** three recurring tasks of a materials engineer: reading phase diagrams, choosing materials, predicting corrosion. Done by hand they are slow and error-prone.
3. **Solution:** one suite with three modules; screenshot of the home page. Every number shows its working.
4. **Architecture:** diagram from `docs/ARCHITECTURE.md`. Say "`core/` has no UI code, so 460+ tests run without a browser".
5. **Theme 1 science:** tiling idea, tie-line, lever rule, pearlite formulas.
6. **Theme 2 science:** performance index M = E^½/ρ, guide line slope 1/p.
7. **Theme 3 science:** ASTM G1 / G102, Tafel intersection, galvanic score, anode sizing.
8. **Live demo** (4 min, script below).
9. **Quality:** 463 tests, boundary cases, ruff, CI, Docker deployment.
10. **Data honesty:** typical textbook values, digitised diagrams (±10 °C), verification sheet signed by the team.
11. **Limitations and next steps:** more diagrams (Al–Si, Fe–Cr), alloying elements, TTT diagrams, multi-objective selection, localized corrosion models. Questions.

## Live demo script
1. **Phase:** Fe–Fe₃C, example *0.35 wt% C, 25 °C*: α + Fe₃C, 94.8% / 5.2%; microstructure 56% ferrite + 44% pearlite. Click the diagram at 1.2 wt% C, 800 °C: γ + Fe₃C. Switch to Cu–Ni and press *Textbook* chip: 68% liquid / 32% α. Type 150 wt% to show the error message.
2. **Selection:** press *Strength ≥ 200 MPa*, objective *Light, stiff beam*: CFRP wins; switch to *Cheap, strong beam*: AISI 1020 steel wins. Explain why cost changes the answer. Set min > max to show validation.
3. **Corrosion:** weight-loss example → 0.0155 mm/y "Outstanding". *Tafel extrapolation → Load example → Calculate*: i_corr ≈ 10 µA/cm², βa 80, βc 120. *Galvanic*: mild steel + copper in seawater: High; change area ratio to 100 and show Severe. *Protection*: steel in seawater: coating + Al–Zn–In anodes, 51.6 kg.
4. **Databases:** add a material with a negative density (error), then a valid one. Show *Verified* toggle. Open *History*.

## Likely questions
* *How do you find the tie-line?* Intersect the phase-field polygon with the horizontal line; the end points are the boundary compositions.
* *Where do the diagram numbers come from?* Digitised from Callister Figs. 9.3a, 9.8, 9.24; the textbook examples reproduce exactly; accuracy ±10 °C, ±1 wt%.
* *Why does a ceramic rank high on strength?* Flexural strength is not yield strength; the app warns about it; toughness is not modelled.
* *Is the galvanic score physical?* It is a qualitative screening score from ΔE, environment and area ratio; real rates need polarization curves.
* *Why NiceGUI?* Python-only GUI with a modern look, matplotlib and Plotly embedding, built on FastAPI so it deploys as a normal web service.
