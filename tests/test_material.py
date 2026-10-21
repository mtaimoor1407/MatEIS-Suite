import dataclasses
import math

import pytest

from core.exceptions import ValidationError
from core.selection.material import LIMITS, Material


def make(**over):
    base = dict(name="Test alloy", material_class="Metal", density_kg_m3=7800,
                youngs_modulus_gpa=200, yield_strength_mpa=300, cost_usd_per_kg=1.5)
    base.update(over)
    return Material(**base)


def test_valid_material_and_derived_values():
    m = make()
    assert m.density_mg_m3 == pytest.approx(7.8)
    assert m.cost_per_volume == pytest.approx(1.5 * 7.8)


def test_name_is_stripped():
    assert make(name="  Steel  ").name == "Steel"


@pytest.mark.parametrize("name", ["", "   ", None])
def test_empty_name_rejected(name):
    with pytest.raises(ValidationError):
        make(name=name)


def test_unknown_class_rejected():
    with pytest.raises(ValidationError):
        make(material_class="Wood")


def test_unknown_strength_basis_rejected():
    with pytest.raises(ValidationError):
        make(strength_basis="shear")


@pytest.mark.parametrize("field", list(LIMITS))
@pytest.mark.parametrize("bad", [0, -1, -0.0001, math.nan, math.inf, -math.inf, "abc", None, True])
def test_invalid_numbers_rejected(field, bad):
    with pytest.raises(ValidationError):
        make(**{field: bad})


@pytest.mark.parametrize("field", list(LIMITS))
def test_numeric_boundaries(field):
    low, high = LIMITS[field]
    assert getattr(make(**{field: low}), field) == low            # lower bound accepted
    assert getattr(make(**{field: high}), field) == high          # upper bound accepted
    with pytest.raises(ValidationError):
        make(**{field: low / 2})                                  # just below
    with pytest.raises(ValidationError):
        make(**{field: high * 1.0001})                            # just above


def test_numeric_strings_are_converted():
    assert make(density_kg_m3="7800").density_kg_m3 == 7800.0


def test_to_record_uses_ashby_units():
    rec = make().to_record()
    assert rec["density"] == pytest.approx(7.8)
    assert rec["modulus"] == 200 and rec["strength"] == 300
    assert rec["cost_vol"] == pytest.approx(11.7)


def test_from_dict_ignores_unknown_keys():
    m = Material.from_dict({**make().to_dict(), "colour": "grey"})
    assert m.name == "Test alloy"


def test_material_is_immutable():
    with pytest.raises(dataclasses.FrozenInstanceError):
        make().name = "other"
