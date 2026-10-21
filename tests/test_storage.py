import pytest

from core.exceptions import MaterialNotFoundError, ValidationError
from core.storage import HistoryStore


@pytest.fixture
def store(tmp_path):
    return HistoryStore(tmp_path / "h.db")


def test_add_list_get_delete(store):
    i = store.add("phase", "Fe-C 0.35 wt% at 700", {"x": 0.35}, {"alpha": 0.95})
    assert store.count() == 1 and store.get(i)["inputs"] == {"x": 0.35}
    store.delete(i)
    with pytest.raises(MaterialNotFoundError):
        store.get(i)


def test_filter_by_theme_and_newest_first(store):
    store.add("phase", "a", {}, {})
    store.add("corrosion", "b", {}, {})
    last = store.add("corrosion", "c", {}, {})
    assert [e["title"] for e in store.list("corrosion")] == ["c", "b"] and store.list()[0]["id"] == last


def test_clear_by_theme_and_all(store):
    store.add("phase", "a", {}, {})
    store.add("selection", "b", {}, {})
    store.clear("phase")
    assert store.count() == 1
    store.clear()
    assert store.count() == 0


@pytest.mark.parametrize("theme,title", [("bogus", "x"), ("phase", ""), ("phase", "   ")])
def test_validation(store, theme, title):
    with pytest.raises(ValidationError):
        store.add(theme, title, {}, {})


def test_non_json_values_are_stringified(store):
    from datetime import date
    i = store.add("phase", "t", {"d": date(2026, 1, 1)}, {})
    assert store.get(i)["inputs"]["d"] == "2026-01-01"
