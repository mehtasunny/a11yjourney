"""Regression tests on real Jetpack Compose captures (see fixtures/compose/README.md)."""
import pathlib
import re

from a11yjourney import audit, load, parse, run
from a11yjourney.reporters import in_scope

FIX = pathlib.Path(__file__).parent / "fixtures" / "compose"


def _conformance(name: str):
    screen = load(str(FIX / f"{name}.xml"))
    large = FIX / f"{name}.large.xml"
    scaled = load(str(large)) if large.exists() else None
    return [f for f in audit(screen, scaled=scaled).findings if in_scope(f)]


def test_accessible_compose_screens_have_no_conformance_findings():
    for name in ("home", "clinic", "trip"):
        assert _conformance(name) == [], name


def test_compose_role_child_is_folded_into_its_clickable_parent():
    screen = load(str(FIX / "home.xml"))
    buttons = [n for n in screen.nodes if n.cls == "Button"]
    assert len(buttons) == 3
    assert all(n.clickable and n.announced for n in buttons)
    assert {n.announced for n in buttons} >= {"Clinic check-in", "Trip planner"}


def test_compose_text_field_label_child_counts_as_its_label():
    screen = load(str(FIX / "clinic.xml"))
    fields = [n for n in screen.nodes if n.editable]
    assert "Full name (required)" in {n.announced for n in fields}


def test_unlabeled_compose_button_is_still_caught():
    xml = (FIX / "home.xml").read_text()
    xml = xml.replace('text="Trip planner"', 'text=""')
    found = [f for f in run(parse(xml)) if f.wcag == "4.1.2"]
    assert len(found) == 1


def test_unlabeled_compose_text_field_is_still_caught():
    xml = (FIX / "clinic.xml").read_text()
    xml = xml.replace('text="Full name (required)"', 'text=""')
    found = [f for f in run(parse(xml)) if f.wcag == "3.3.2"]
    assert len(found) == 1


def test_elements_cut_off_at_the_bottom_are_not_size_checked():
    screen = load(str(FIX / "trip.xml"))
    clipped = [n for n in screen.nodes if n.clipped and n.actionable]
    assert clipped and all(n.bounds[3] >= screen.height for n in clipped)


def test_side_by_side_fields_of_different_heights_read_left_to_right():
    screen = load(str(FIX / "clinic.xml"))
    order = [n.announced for n in screen.visual_order() if n.editable]
    labels = [re.sub(r"\s.*", "", o) for o in order]
    assert labels[1:4] == ["Month", "Day", "Year"]
