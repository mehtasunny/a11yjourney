from a11yjourney import audit, parse
from conftest import tree


def _pair(base_nodes, large_nodes):
    return parse(tree(base_nodes)), parse(tree(large_nodes))


def _resize(base, large):
    return [f for f in audit(base, scaled=large).findings if f.wcag == "1.4.4"]


GROWS = [
    {"text": "Your trips", "rid": "title", "bounds": (40, 100, 800, 160)},
    {"text": "Route 7 to Downtown", "rid": "r1", "bounds": (40, 300, 800, 360)},
]
GROWN = [
    {"text": "Your trips", "rid": "title", "bounds": (40, 100, 800, 220)},
    {"text": "Route 7 to Downtown", "rid": "r1", "bounds": (40, 300, 800, 420)},
]


def test_clean_scaling_has_no_findings():
    base, large = _pair(GROWS, GROWN)
    assert _resize(base, large) == []


def test_text_that_does_not_grow_is_flagged_for_review():
    base, large = _pair(
        GROWS + [{"cls": "Button", "text": "Check in", "rid": "checkin", "clickable": True,
                  "bounds": (40, 600, 400, 744)}],
        GROWN + [{"cls": "Button", "text": "Check in", "rid": "checkin", "clickable": True,
                  "bounds": (40, 600, 400, 744)}],
    )
    f = _resize(base, large)
    assert [x.element for x in f] == ["checkin"]
    assert f[0].severity.value == "moderate" and f[0].review


def test_new_overlap_is_serious():
    base, large = _pair(
        GROWS + [{"text": "Arrives 5:42", "rid": "eta", "bounds": (40, 170, 500, 230)}],
        GROWN + [{"text": "Arrives 5:42", "rid": "eta", "bounds": (40, 190, 500, 330)}],
    )
    f = _resize(base, large)
    assert any("overlaps" in x.message and x.severity.value == "serious" for x in f)


def test_missing_text_outside_scroll_is_serious_but_inside_scroll_is_ignored():
    fixed = {"text": "Copay $20", "rid": "copay", "bounds": (40, 900, 600, 960)}
    scroller = {"cls": "ScrollView", "rid": "list", "scrollable": True,
                "bounds": (0, 1000, 1080, 2000),
                "children": [{"text": "Dr. Lee, 3pm", "rid": "appt",
                              "bounds": (40, 1900, 600, 1960)}]}
    base, large = _pair(GROWS + [fixed, scroller], GROWN)
    f = _resize(base, large)
    assert {x.element for x in f} == {"copay"}


def test_unapplied_font_scale_is_detected_and_skipped():
    base, large = _pair(GROWS, GROWS)
    result = audit(base, scaled=large)
    assert not [f for f in result.findings if f.wcag == "1.4.4"]
    assert any("may not have been applied" in n for n in result.notes)
