from a11yjourney import parse, run
from conftest import tree


def _ids(nodes):
    return [(f.wcag, f.element) for f in run(parse(tree(nodes)))]


def test_duplicate_labels_on_separate_controls():
    found = _ids([
        {"cls": "Button", "text": "Remove", "rid": "a", "clickable": True,
         "bounds": (40, 100, 540, 250)},
        {"cls": "Button", "text": "Remove", "rid": "b", "clickable": True,
         "bounds": (40, 300, 540, 450)},
    ])
    assert ("2.4.6", "Remove") in found


def test_unclear_purpose_link_and_button():
    found = _ids([
        {"cls": "TextView", "text": "Learn more", "rid": "more", "clickable": True,
         "bounds": (40, 100, 540, 250)},
        {"cls": "Button", "text": "Click here", "rid": "go", "clickable": True,
         "bounds": (40, 300, 540, 450)},
    ])
    assert ("2.4.4", "more") in found
    assert ("2.4.6", "go") in found


def test_redundant_role_in_label():
    found = _ids([{"cls": "ImageButton", "desc": "Close button", "rid": "x",
                   "clickable": True, "bounds": (40, 100, 200, 260)}])
    assert ("android-redundant-role", "x") in found


def test_duplicate_clickable_bounds():
    found = _ids([{"cls": "FrameLayout", "rid": "row", "clickable": True,
                   "bounds": (0, 100, 1080, 300),
                   "children": [{"cls": "Button", "text": "Open", "rid": "open",
                                 "clickable": True, "bounds": (0, 100, 1080, 300)}]}])
    assert any(w == "android-duplicate-clickable" for w, _ in found)


def test_content_description_on_editable_field():
    found = _ids([{"cls": "EditText", "desc": "Email", "rid": "email", "clickable": True,
                   "bounds": (40, 100, 1040, 260)}])
    assert ("android-editable-description", "email") in found


def test_clean_controls_have_no_pattern_findings():
    found = _ids([
        {"cls": "Button", "text": "Check in", "rid": "a", "clickable": True,
         "bounds": (40, 100, 540, 250)},
        {"cls": "ImageButton", "desc": "Close map", "rid": "b", "clickable": True,
         "bounds": (600, 100, 760, 260)},
    ])
    assert not [f for f in found if f[0] in ("2.4.4", "2.4.6") or f[0].startswith("android-")
                and f[0] != "android-touch-target"]
