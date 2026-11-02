"""Regression tests from OneBusAway captures (see fixtures/oba/README.md)."""
import json
import pathlib

from a11yjourney import audit, load

FIX = pathlib.Path(__file__).parent / "fixtures" / "oba"


def _audit(name, trace=None):
    screen = load(str(FIX / f"{name}.xml"))
    focus = json.loads((FIX / f"{trace}.focus.json").read_text()) if trace else None
    return audit(screen, focus_trace=focus)


def test_one_button_dialog_is_not_a_keyboard_trap():
    result = _audit("dialog", "dialog")
    assert [f for f in result.findings if f.wcag == "2.1.2"] == []
    assert any("single control" in n for n in result.notes)


def test_focus_on_an_element_missing_from_the_capture_is_not_judged():
    result = _audit("home", "home")
    assert [f for f in result.findings if f.wcag == "2.1.2"] == []
    assert any("not in this capture" in n for n in result.notes)


def test_live_countdown_still_matches_its_focus_stop():
    result = _audit("arrivals", "arrivals")
    assert [f for f in result.findings if f.wcag == "2.1.1"] == []


def test_disabled_unfocusable_views_are_not_reported():
    result = _audit("arrivals")
    assert [f for f in result.findings if f.wcag in ("4.1.2", "2.5.5", "2.5.8")] == []
    assert any("inactive" in n for n in result.notes)


def test_unnamed_switch_on_the_published_settings_screen_is_still_caught():
    published = [f for f in _audit("settings-published").findings if f.wcag == "4.1.2"]
    fixed = [f for f in _audit("settings-fixed").findings if f.wcag == "4.1.2"]
    assert len(published) == 1
    assert fixed == []
