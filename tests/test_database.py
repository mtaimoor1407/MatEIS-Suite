import json
import sqlite3

import pytest

from core.exceptions import DatabaseError, DuplicateMaterialError, MaterialNotFoundError, ValidationError
from core.selection.database import MaterialDatabase
from core.selection.material import Material


def sample(name="Sample"):
    return Material(name=name, material_class="Polymer", density_kg_m3=1000,
                    youngs_modulus_gpa=2, yield_strength_mpa=40, cost_usd_per_kg=2)


def test_seed_loads_all_materials(db):
    assert db.count() >= 15


def test_seeding_twice_does_not_duplicate(db, seed_path):
    before = db.count()
    assert db.seed_from_json(seed_path) == 0
    assert db.count() == before


def test_replace_seed_resets_table(db, seed_path):
    db.add(sample())
    db.seed_from_json(seed_path, replace=True)
    assert "Sample" not in [m.name for m in db.list_materials()]


def test_add_get_update_delete(db):
    added = db.add(sample())
    assert db.get(added.id).name == "Sample"
    updated = db.update(added.id, sample("Renamed"))
    assert updated.name == "Renamed"
    db.delete(added.id)
    with pytest.raises(MaterialNotFoundError):
        db.get(added.id)


def test_duplicate_name_rejected(db):
    db.add(sample())
    with pytest.raises(DuplicateMaterialError):
        db.add(sample())


def test_update_to_existing_name_rejected(db):
    a = db.add(sample("A"))
    db.add(sample("B"))
    with pytest.raises(DuplicateMaterialError):
        db.update(a.id, sample("B"))


@pytest.mark.parametrize("op", ["get", "delete", "verify"])
def test_missing_id_raises(db, op):
    with pytest.raises(MaterialNotFoundError):
        {"get": lambda: db.get(99999), "delete": lambda: db.delete(99999),
         "verify": lambda: db.set_verified(99999, True)}[op]()


def test_set_verified(db):
    m = db.list_materials()[0]
    db.set_verified(m.id, True)
    assert db.get(m.id).verified is True


def test_sql_injection_text_is_stored_literally(db):
    nasty = "x'); DROP TABLE materials;--"
    db.add(sample(nasty))
    assert db.get(db.add(sample("after")).id).name == "after"
    assert nasty in [m.name for m in db.list_materials()]


def test_database_check_constraints_block_bad_rows(db):
    with sqlite3.connect(db.db_path) as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO materials (name, material_class, density_kg_m3, youngs_modulus_gpa, "
                         "yield_strength_mpa, cost_usd_per_kg) VALUES ('bad','Metal',-5,1,1,1)")


def test_dataframe_columns_and_units(df):
    assert {"name", "density", "modulus", "strength", "cost", "cost_vol"} <= set(df.columns)
    steel = df[df["name"].str.contains("1020")].iloc[0]
    assert steel["density"] == pytest.approx(7.87)


def test_empty_database_gives_empty_dataframe(tmp_path):
    empty = MaterialDatabase(tmp_path / "e.db").to_dataframe()
    assert empty.empty and "modulus" in empty.columns


def test_invalid_seed_file_is_rejected(tmp_path, db):
    missing = tmp_path / "nope.json"
    with pytest.raises(DatabaseError):
        db.seed_from_json(missing)
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    with pytest.raises(DatabaseError):
        db.seed_from_json(bad)
    notlist = tmp_path / "obj.json"
    notlist.write_text("{}")
    with pytest.raises(ValidationError):
        db.seed_from_json(notlist)


def test_seed_with_invalid_row_changes_nothing(tmp_path, db):
    before = db.count()
    path = tmp_path / "s.json"
    path.write_text(json.dumps([sample("ok").to_dict(), {**sample("bad").to_dict(), "density_kg_m3": -1}]))
    with pytest.raises(ValidationError):
        db.seed_from_json(path, replace=True)
    assert db.count() == before
