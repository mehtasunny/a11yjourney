import json

import pytest

from a11yjourney.cli import main
from a11yjourney.imaging import encode
from a11yjourney.journey import (
    JourneyError,
    Session,
    explore,
    find,
    parse_steps,
    run_journey,
    signature,
)
from a11yjourney.model import parse
from conftest import tree

SCREENS = {
    "home": [
        {"cls": "Button", "text": "Clinic check-in", "rid": "clinic", "clickable": True,
         "bounds": (40, 200, 1040, 350), "goto": "clinic"},
        {"cls": "Button", "text": "Delete account", "rid": "delete", "clickable": True,
         "bounds": (40, 400, 1040, 550), "goto": "deleted"},
        {"cls": "Button", "text": "Trip planner", "rid": "trip", "clickable": True,
         "bounds": (40, 600, 1040, 750), "goto": "trip"},
        {"cls": "Button", "text": "About", "rid": "about", "clickable": True,
         "bounds": (40, 800, 1040, 950)},
    ],
    "clinic": [{"cls": "TextView", "text": "Clinic check-in", "bounds": (40, 100, 1040, 200)},
               {"cls": "EditText", "rid": "name", "hint": "", "clickable": True,
                "bounds": (40, 300, 1040, 450)}],
    "trip": [{"cls": "TextView", "text": "Trip planner", "bounds": (40, 100, 1040, 200)}],
    "deleted": [{"cls": "TextView", "text": "Account deleted", "bounds": (40, 100, 1040, 200)}],
}


class FakeDevice:
    def __init__(self):
        self.stack = ["home"]
        self.typed = []
        self.scale = "1.0"

    def xml(self):
        return tree([{k: v for k, v in n.items() if k != "goto"}
                     for n in SCREENS[self.stack[-1]]], density=None)

    def __call__(self, args):
        cmd = " ".join(args)
        if cmd == "shell wm density":
            return b"Physical density: 480"
        if cmd.startswith("shell uiautomator dump"):
            return b"UI hierchary dumped to: /sdcard/x.xml"
        if cmd.startswith("shell cat"):
            return self.xml().encode()
        if cmd == "exec-out screencap -p":
            return encode(2, 2, [(255, 255, 255)] * 4)
        if cmd.startswith("shell settings get"):
            return self.scale.encode()
        if cmd.startswith("shell settings put"):
            self.scale = args[-1]
            return b""
        if cmd.startswith("shell input tap"):
            x, y = int(args[3]), int(args[4])
            for n in SCREENS[self.stack[-1]]:
                x1, y1, x2, y2 = n["bounds"]
                if x1 <= x <= x2 and y1 <= y <= y2 and n.get("goto"):
                    self.stack.append(n["goto"])
            return b""
        if cmd == "shell input keyevent KEYCODE_BACK":
            if len(self.stack) > 1:
                self.stack.pop()
            return b""
        if cmd.startswith("shell input text"):
            self.typed.append(args[-1])
            return b""
        if cmd.startswith(("shell am start", "shell monkey")):
            self.stack = ["home"]
            return b""
        return b""


def _session(tmp_path, dev):
    return Session(dev, tmp_path, sleep=lambda _s: None)


def test_find_prefers_exact_then_clickable():
    s = parse(tree(SCREENS["home"]))
    assert find(s, "Trip planner").rid == "trip"
    assert find(s, "trip").rid == "trip"
    assert find(s, "nothing here") is None


def test_journey_runs_steps_and_captures(tmp_path):
    dev = FakeDevice()
    steps = parse_steps('''
        # check in
        launch org.example/.Main
        capture home nolarge
        tap "Clinic check-in"
        type "Jane Test"
        capture clinic
        back
    ''')
    captured = run_journey(_session(tmp_path, dev), steps)
    assert [c.rsplit("/", 1)[-1] for c in captured] == ["home.xml", "clinic.xml"]
    assert dev.typed == ["Jane%sTest"] and dev.stack == ["home"]
    assert (tmp_path / "clinic.large.xml").exists() and not (tmp_path / "home.large.xml").exists()
    assert json.loads((tmp_path / "journey.json").read_text())["captures"]


def test_journey_reports_the_failing_step(tmp_path):
    with pytest.raises(JourneyError, match="step 2"):
        run_journey(_session(tmp_path, FakeDevice()),
                    parse_steps('capture home nolarge\ntap "Nope"'))


def test_explore_captures_new_screens_and_skips_risky_controls(tmp_path):
    dev = FakeDevice()
    result = explore(_session(tmp_path, dev), max_screens=5)
    visits = {v["control"]: v["result"] for v in result["visits"]}
    assert visits["Delete account"].startswith("skipped")
    assert visits["Clinic check-in"].startswith("captured")
    assert visits["Trip planner"].startswith("captured")
    assert visits["About"] == "no new screen"
    assert len(result["captures"]) == 3 and dev.stack == ["home"]


def test_signature_ignores_positions():
    a = parse(tree(SCREENS["home"]))
    moved = [dict(n, bounds=(n["bounds"][0], n["bounds"][1] + 5, n["bounds"][2],
                             n["bounds"][3] + 5)) for n in SCREENS["home"]]
    assert signature(a) == signature(parse(tree(moved)))


def test_report_audits_a_folder(tmp_path, capsys):
    dev = FakeDevice()
    run_journey(_session(tmp_path, dev),
                parse_steps('capture home nolarge\ntap "Clinic check-in"\ncapture clinic nolarge'))
    assert main(["report", str(tmp_path)]) in (0, 1)
    out = capsys.readouterr().out
    assert "home" in out and "clinic" in out
    assert main(["report", str(tmp_path), "--format", "sarif"]) in (0, 1)
    doc = json.loads(capsys.readouterr().out)
    uris = {r["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
            for r in doc["runs"][0]["results"]}
    assert any(u.endswith("clinic.xml") for u in uris)
