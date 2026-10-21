"""End-to-end UI tests with NiceGUI's simulated user (no browser needed)."""
import pytest
from nicegui import ui
from nicegui.testing import User

from core.exceptions import ValidationError
from ui.components.parsing import parse_polarization


@pytest.mark.parametrize("path,text", [("/", "Three tools for the"), ("/phase", "Phases present"), ("/selection", "Design constraints"),
                                       ("/corrosion", "Method and material"), ("/data", "Add material"), ("/history", "History"),
                                       ("/guide", "Requirements of the project document")])
async def test_every_page_renders(user: User, path: str, text: str):
    await user.open(path)
    await user.should_see(text)


async def test_phase_page_shows_lever_rule_and_microstructure(user: User):
    await user.open("/phase")
    await user.should_see("Hypoeutectoid steel")
    await user.should_see("Lever rule, step by step")
    await user.should_see("Pearlite")


async def test_phase_page_switches_diagram(user: User):
    await user.open("/phase")
    next(iter(user.find(kind=ui.toggle).elements)).set_value("pb_sn")
    await user.should_see("Pb-rich")
    await user.should_see("Hypoeutectic")


async def test_selection_page_ranks_materials(user: User):
    await user.open("/selection")
    await user.should_see("Best material")
    await user.should_see("CFRP unidirectional")


async def test_selection_preset_filters_candidates(user: User):
    await user.open("/selection")
    user.find("Strength ≥ 200 MPa").click()
    await user.should_see("16")


async def test_corrosion_weight_loss_calculation(user: User):
    await user.open("/corrosion")
    user.find(kind=ui.button, content="Calculate").click()
    await user.should_see("Outstanding")
    await user.should_see("0.0155")


async def test_corrosion_galvanic_assessment(user: User):
    await user.open("/corrosion")
    user.find("2  Galvanic risk").click()
    user.find(kind=ui.button, content="Assess risk").click()
    await user.should_see("Carbon / mild steel")
    await user.should_see("High")


async def test_corrosion_protection_plan_with_anode_sizing(user: User):
    await user.open("/corrosion")
    user.find("3  Protection plan").click()
    user.find(kind=ui.button, content="Generate plan").click()
    await user.should_see("Sacrificial anode sizing")
    await user.should_see("Anode mass")


# ---- parser used by the Tafel input box ----------------------------------------------------------
def test_parse_polarization_accepts_header_and_mixed_separators():
    text = "E (V), i (A/cm2)\n" + "\n".join(f"{-0.3 + 0.01 * k}; {1e-6 * (k + 1)}" for k in range(8))
    e, i = parse_polarization(text)
    assert len(e) == 8 and i[0] == 1e-6


@pytest.mark.parametrize("text", ["", "1, 2\n3, 4", "a, b\nc, d\n" + "1, 2\n" * 7 + "bad line here"])
def test_parse_polarization_rejects_bad_input(text):
    with pytest.raises(ValidationError):
        parse_polarization(text)
