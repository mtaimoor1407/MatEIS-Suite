import math

import pytest

from core.exceptions import ValidationError
from core.selection.filters import Constraints, apply_constraints


def test_no_constraints_returns_everything(df):
    assert len(apply_constraints(df, Constraints())) == len(df)


def test_document_example_yield_above_200(df):
    out = apply_constraints(df, Constraints(ranges={"strength": (200, None)}))
    assert (out["strength"] >= 200).all() and 0 < len(out) < len(df)


def test_bounds_are_inclusive(df):
    exact = float(df[df["name"].str.contains("6061")]["strength"].iloc[0])
    out = apply_constraints(df, Constraints(ranges={"strength": (exact, exact)}))
    assert any("6061" in n for n in out["name"])


def test_just_above_boundary_excludes(df):
    exact = float(df[df["name"].str.contains("6061")]["strength"].iloc[0])
    out = apply_constraints(df, Constraints(ranges={"strength": (exact + 1e-9, exact + 1e-9)}))
    assert not any("6061" in n for n in out["name"])


def test_class_filter(df):
    out = apply_constraints(df, Constraints(classes=("Polymer",)))
    assert set(out["material_class"]) == {"Polymer"}


def test_combined_constraints(df):
    c = Constraints(classes=("Metal", "Composite"), ranges={"density": (None, 3.0), "strength": (250, None)})
    out = apply_constraints(df, c)
    assert (out["density"] <= 3.0).all() and (out["strength"] >= 250).all()


def test_impossible_constraints_give_empty_not_error(df):
    assert apply_constraints(df, Constraints(ranges={"strength": (1e12, None)})).empty


def test_filter_does_not_modify_input(df):
    before = len(df)
    apply_constraints(df, Constraints(ranges={"strength": (500, None)}))
    assert len(df) == before


@pytest.mark.parametrize("bounds", [(-1, None), (None, -5), (math.nan, None), (None, math.inf), ("a", None), (True, None)])
def test_invalid_bounds_rejected(df, bounds):
    with pytest.raises(ValidationError):
        apply_constraints(df, Constraints(ranges={"modulus": bounds}))


def test_min_greater_than_max_rejected(df):
    with pytest.raises(ValidationError):
        apply_constraints(df, Constraints(ranges={"modulus": (100, 50)}))


def test_min_equal_max_allowed(df):
    apply_constraints(df, Constraints(ranges={"modulus": (100, 100)}))


def test_unknown_property_and_class_rejected(df):
    with pytest.raises(ValidationError):
        apply_constraints(df, Constraints(ranges={"hardness": (1, 2)}))
    with pytest.raises(ValidationError):
        apply_constraints(df, Constraints(classes=("Wood",)))


def test_empty_class_selection_rejected(df):
    with pytest.raises(ValidationError):
        apply_constraints(df, Constraints(classes=()))


def test_describe_lists_limits():
    text = " ".join(Constraints(ranges={"strength": (200, 900)}).describe())
    assert "≥ 200" in text and "≤ 900" in text
