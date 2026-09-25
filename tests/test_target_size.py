from a11yjourney import audit, parse, run
from conftest import tree


def _find(findings, element):
    return [f for f in findings if f.element == element]


def test_isolated_small_target_meets_spacing_exception():
    # 60x60px at density 3 = 20dp, far from anything else
    s = parse(tree([{"cls": "ImageButton", "rid": "help", "desc": "Help", "clickable": True,
                     "bounds": (500, 1000, 560, 1060)}]))
    ids = {f.wcag for f in _find(run(s), "help")}
    assert ids == {"2.5.5"}


def test_crowded_small_target_fails_2_5_8():
    s = parse(tree([
        {"cls": "ImageButton", "rid": "a", "desc": "Zoom in", "clickable": True,
         "bounds": (500, 1000, 560, 1060)},
        {"cls": "ImageButton", "rid": "b", "desc": "Zoom out", "clickable": True,
         "bounds": (570, 1000, 630, 1060)},
    ]))
    assert {f.wcag for f in _find(run(s), "a")} == {"2.5.8"}


def test_between_44_and_48dp_is_android_guidance_only():
    # 138px / 3 = 46dp
    s = parse(tree([{"cls": "Button", "rid": "go", "text": "Plan trip", "clickable": True,
                     "bounds": (100, 100, 238, 238)}]))
    assert {f.wcag for f in _find(run(s), "go")} == {"android-touch-target"}


def test_unknown_density_skips_sizes_with_a_note():
    s = parse(tree([{"cls": "ImageButton", "rid": "x", "desc": "Close", "clickable": True,
                     "bounds": (0, 0, 60, 60)}], density=None))
    result = audit(s)
    assert not [f for f in result.findings if f.wcag in ("2.5.8", "2.5.5")]
    assert any("density unknown" in n for n in result.notes)


def test_density_argument_fills_in_missing_density():
    xml = tree([{"cls": "ImageButton", "rid": "x", "desc": "Close", "clickable": True,
                 "bounds": (0, 0, 60, 60)}], density=None)
    s = parse(xml, density=3.0)
    assert s.density_known and abs(s.nodes[1].w_dp - 20) < 0.01
