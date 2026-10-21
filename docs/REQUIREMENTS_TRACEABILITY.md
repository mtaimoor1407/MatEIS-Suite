# Requirements traceability

Every statement of the project document and where it is satisfied.

## General
| Requirement | Evidence |
|---|---|
| GUI application in Python (desktop or web) | `main.py`, `ui/` (NiceGUI, Python only) |
| Practical materials problem / interactive learning tool | Three modules |
| Teams of 2–3 (2024, 2023, 2026 sessions) | Fill in `config.py` and README |
| numpy / pandas backend, matplotlib charts embedded | `core/`; *Matplotlib view* tab; PDF reports |
| JSON or sqlite3 storage for properties or history | SQLite, seeded from JSON; History table |

## Theme 1 – Phase Diagram Interactive Simulator
| Core feature | Evidence |
|---|---|
| Plot binary diagrams (Fe-C, Cu-Ni), input composition X and temperature T | Fe–Fe₃C, Cu–Ni, Pb–Sn; sliders, boxes, click-on-diagram |
| Clean plot of the diagram | Plotly and matplotlib versions, labelled fields and invariant lines |
| Dynamic lever-rule phase amounts | `PhaseDiagram.equilibrium`; table, bar and worked arithmetic |
| Microstructure schematic / description (pearlite vs proeutectoid ferrite) | `microstructure.py`, `schematic.py` |

## Theme 2 – Materials Selection & Ashby Plotter
| Core feature | Evidence |
|---|---|
| ≥ 15 materials (metals, polymers, ceramics, composites) with density, E, yield strength, cost | 26 materials; `tests/test_seed_data.py` |
| Filters for design constraints | `core/selection/filters.py` |
| Interactive plot of two properties highlighting the optimal material for a performance index | `ui/figures/selection.py` |

## Theme 3 – Corrosion Rate & Kinetics Calculator
| Core feature | Evidence |
|---|---|
| Rate in mm/year or mils/year from weight loss | `weight_loss_rate` |
| Rate from electrochemical inputs (Tafel extrapolation) | `tafel_extrapolation`, `electrochemical_rate`, `stern_geary` |
| Galvanic risk from an interactive EMF series database | `EMFDatabase`, `assess_couple`, Databases page |
| Recommendations report (sacrificial anodes, coatings) | `recommend`, `size_anodes`, `corrosion_pdf` |

## Timeline items
| Item | Evidence |
|---|---|
| Formulas, backend with numpy / pandas | `core/`, `docs/ARCHITECTURE.md` |
| GUI and matplotlib charts | `ui/`, `core/phase/plotting.py` |
| Integration, JSON / sqlite3 storage | `core/selection/database.py`, `core/storage.py` |
| Boundary value testing | `tests/` (463 tests) |
| Documentation, user guide, presentation | `README.md`, `docs/` |

## Grading rubric
| Criterion (weight) | How it is met |
|---|---|
| Materials science accuracy (30%) | Textbook worked examples reproduce; ASTM constants; cited data; `DATA_VERIFICATION.md`; stated limitations |
| Code architecture and logic (25%) | OOP dataclasses and classes, `core/` free of UI code, custom exceptions, numpy/pandas/matplotlib, ruff-clean |
| UI/UX and functionality (15%) | Dark/light themes, per-module accent colours, live updates, click-to-select, friendly errors, exports |
| Documentation and comments (10%) | README, user guide, architecture, deployment, docstrings |
| Final presentation and demo (10%) | `PRESENTATION_OUTLINE.md`, hosted link, local backup |
| Video documentation (10%) | `VIDEO_SCRIPT.md` |
