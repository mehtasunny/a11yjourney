from a11yjourney import audit, parse
from a11yjourney.imaging import decode, encode
from conftest import tree

W, H = 540, 400
WHITE = (255, 255, 255)


def _image(fills):
    """fills: list of (x1, y1, x2, y2, color, glyph) drawn on white. glyph=True draws
    text-like vertical strokes with an anti-aliased edge instead of a solid block."""
    px = [WHITE] * (W * H)
    for x1, y1, x2, y2, color, glyph in fills:
        for y in range(y1, y2):
            for x in range(x1, x2):
                if not glyph:
                    px[y * W + x] = color
                elif (x - x1) % 12 in (0, 1, 2):
                    px[y * W + x] = color
                elif (x - x1) % 12 == 3:  # anti-aliased edge
                    px[y * W + x] = tuple((c + 255) // 2 for c in color)
    return decode(encode(W, H, px))


def _audit(nodes, fills):
    screen = parse(tree(nodes, width=W, height=H))
    return audit(screen, image=_image(fills))


def test_low_contrast_text_is_serious():
    r = _audit([{"text": "Next bus 5 min", "rid": "eta", "bounds": (20, 20, 320, 70)}],
               [(30, 30, 300, 60, (0xAA, 0xAA, 0xAA), True)])
    f = [x for x in r.findings if x.wcag == "1.4.3"]
    assert f and f[0].severity.value == "serious" and f[0].review


def test_borderline_text_is_moderate_large_text_caveat():
    r = _audit([{"text": "Refill due", "rid": "due", "bounds": (20, 20, 320, 70)}],
               [(30, 30, 300, 60, (0x88, 0x88, 0x88), True)])
    f = [x for x in r.findings if x.wcag == "1.4.3"]
    assert f and f[0].severity.value == "moderate" and "large-scale" in f[0].message


def test_good_contrast_passes():
    r = _audit([{"text": "Appointments", "rid": "t", "bounds": (20, 20, 320, 70)}],
               [(30, 30, 300, 60, (0x22, 0x22, 0x22), True)])
    assert not [x for x in r.findings if x.wcag == "1.4.3"]


def test_faint_icon_button_fails_non_text_contrast():
    r = _audit([{"cls": "ImageButton", "rid": "menu", "desc": "Menu", "clickable": True,
                 "bounds": (400, 20, 544 - 4, 164)}],
               [(430, 50, 510, 134, (0xDD, 0xDD, 0xDD), True)])
    assert [x for x in r.findings if x.wcag == "1.4.11"]


def test_disabled_controls_are_exempt():
    r = _audit([{"cls": "Button", "text": "Submit", "rid": "s", "enabled": False,
                 "clickable": True, "bounds": (20, 100, 320, 250)}],
               [(30, 130, 300, 200, (0xCC, 0xCC, 0xCC), True)])
    assert not [x for x in r.findings if x.wcag == "1.4.3"]


def test_mismatched_screenshot_is_skipped_with_note():
    screen = parse(tree([{"text": "Hi", "bounds": (0, 0, 900, 60)}], width=1080, height=2160))
    r = audit(screen, image=_image([]))
    assert any("contrast checks skipped" in n for n in r.notes)
