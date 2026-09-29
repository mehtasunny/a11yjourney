from a11yjourney import audit, parse
from a11yjourney.capture import focus_walk
from a11yjourney.keyboard import analyze, node_key
from conftest import tree

NODES = [
    {"cls": "EditText", "rid": "name", "desc": "", "clickable": True,
     "bounds": (40, 100, 1040, 260)},
    {"cls": "EditText", "rid": "phone", "clickable": True, "bounds": (40, 300, 1040, 460)},
    {"cls": "Button", "text": "Check in", "rid": "go", "clickable": True,
     "bounds": (40, 500, 1040, 650)},
]


def _screen():
    return parse(tree(NODES))


def _trace(keys, wrapped=True, stuck=False):
    return {"steps": [{"key": k} for k in keys], "wrapped": wrapped, "stuck": stuck}


def test_full_cycle_in_visual_order_is_clean():
    f, notes = analyze(_screen(), _trace(["id:name", "id:phone", "id:go|Check in", "id:name"]))
    assert f == []
    assert any("cycle complete" in n for n in notes)


def test_control_never_reached_by_tab():
    f, _ = analyze(_screen(), _trace(["id:name", "id:phone", "id:name"]))
    assert [(x.wcag, x.element) for x in f] == [("2.1.1", "go")]


def test_focus_trap():
    f, _ = analyze(_screen(), _trace(["id:name", "id:phone", "id:phone", "id:phone"],
                                     wrapped=False, stuck=True))
    assert [x.wcag for x in f] == ["2.1.2"]


def test_measured_order_that_jumps_up():
    f, _ = analyze(_screen(), _trace(["id:name", "id:go|Check in", "id:phone", "id:name"]))
    assert ("2.4.3", "phone") in [(x.wcag, x.element) for x in f]


def test_no_focus_at_all():
    f, _ = analyze(_screen(), {"steps": [{"key": None}] * 5, "wrapped": False})
    assert [x.wcag for x in f] == ["2.1.1"]


def test_measured_trace_replaces_inferred_focus_order():
    screen = _screen()
    inferred = [x for x in audit(screen).findings if x.wcag == "2.4.3"]
    trace = _trace(["id:name", "id:phone", "id:go|Check in", "id:name"])
    measured = audit(screen, focus_trace=trace)
    assert not [x for x in measured.findings if x.wcag == "2.4.3" and x.kind != "KEYBOARD"]
    assert inferred == [] or inferred[0].kind == "SEMANTIC"


class TabAdb:
    """Moves focus through the given element ids, one per Tab press."""

    def __init__(self, order):
        self.order = order
        self.presses = 0

    def __call__(self, args):
        cmd = " ".join(args)
        if cmd == "shell input keyevent KEYCODE_TAB":
            self.presses += 1
            return b""
        if cmd.startswith("shell uiautomator dump"):
            return b"UI hierchary dumped to: /sdcard/a11yjourney_dump.xml"
        if cmd.startswith("shell cat"):
            focus = self.order[(self.presses - 1) % len(self.order)] if self.presses else None
            xml = tree(NODES, density=None)
            if focus:
                rid = f'org.example:id/{focus}"'
                xml = xml.replace(rid, rid + ' focused="true"')
            return xml.encode()
        return b""


def test_focus_walk_detects_a_full_cycle():
    trace = focus_walk(TabAdb(["name", "phone", "go"]), 3.0, sleep=lambda _s: None)
    keys = [s["key"] for s in trace["steps"]]
    assert keys == ["id:name", "id:phone", "id:go|Check in", "id:name"]
    assert trace["wrapped"] and not trace["stuck"]


def test_focus_walk_detects_a_trap():
    trace = focus_walk(TabAdb(["name", "phone", "phone", "phone", "phone", "phone"]), 3.0,
                       sleep=lambda _s: None)
    assert trace["stuck"] and not trace["wrapped"]


def test_node_key_prefers_resource_id():
    n = _screen().nodes[1]
    assert node_key(n) == "id:name"


def test_list_items_sharing_an_id_are_told_apart():
    screen = parse(tree([
        {"cls": "TextView", "text": "Asia", "rid": "item", "clickable": True,
         "bounds": (0, 100, 1080, 250)},
        {"cls": "TextView", "text": "Europe", "rid": "item", "clickable": True,
         "bounds": (0, 260, 1080, 410)},
    ]))
    assert node_key(screen.nodes[1]) != node_key(screen.nodes[2])
