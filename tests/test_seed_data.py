"""Guards the dataset requirements from the project document and catches typos."""
import json
from pathlib import Path

import pytest

DATA = json.loads((Path(__file__).resolve().parent.parent / "data" / "materials_seed.json").read_text("utf-8"))


def test_at_least_15_materials_and_all_four_classes():
    assert len(DATA) >= 15
    assert {m["material_class"] for m in DATA} == {"Metal", "Polymer", "Ceramic", "Composite"}


def test_names_unique_and_sources_present():
    names = [m["name"] for m in DATA]
    assert len(names) == len(set(names))
    assert all(m["source"] for m in DATA)


@pytest.mark.parametrize("m", DATA, ids=lambda m: m["name"])
def test_plausible_ranges_per_class(m):
    rho, E = m["density_kg_m3"], m["youngs_modulus_gpa"]
    ranges = {"Metal": ((1500, 9500), (30, 260)), "Polymer": ((800, 1500), (0.1, 10)),
              "Ceramic": ((2000, 6500), (50, 450)), "Composite": ((1300, 2200), (10, 250))}
    (rlo, rhi), (elo, ehi) = ranges[m["material_class"]]
    assert rlo <= rho <= rhi and elo <= E <= ehi


def test_spot_checks_against_textbook_values():
    by = {m["name"]: m for m in DATA}
    assert by["Aluminum 6061-T6"]["youngs_modulus_gpa"] == 69
    assert by["Aluminum 6061-T6"]["yield_strength_mpa"] == 275
    assert by["Titanium Ti-6Al-4V (annealed)"]["youngs_modulus_gpa"] == 114
    assert 7800 <= by["AISI 4140 Steel (normalized)"]["density_kg_m3"] <= 7900


def test_every_row_ships_unverified():
    assert not any(m["verified"] for m in DATA)
