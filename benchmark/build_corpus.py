"""Generate the labeled benchmark corpus from declarative specs.

Ground truth is declared here, independently of the engine, so the benchmark
measures real recovery rather than echoing the engine back at itself. Each
element may declare `defects` (WCAG ids) that represent genuine accessibility
problems a human auditor would confirm on that screen.
"""
from __future__ import annotations

import json
import pathlib

STATIC = {"4.1.2", "3.3.2", "2.5.8"}  # presence/absence, catchable by static scanners
JUDGMENT = {"2.4.6", "2.4.3", "1.1.1"}  # require meaning / flow judgment

DENSITY = 3.0


def ident(e: dict) -> str:
    return e.get("rid") or e.get("desc") or e.get("text") or e.get("cls") or "unknown"


def node_xml(i: int, e: dict) -> str:
    x1, y1, x2, y2 = e["bounds"]
    attrs = {
        "index": str(i),
        "text": e.get("text", ""),
        "resource-id": (f"com.example.app:id/{e['rid']}" if e.get("rid") else ""),
        "class": "android.widget." + e["cls"],
        "content-desc": e.get("desc", ""),
        "clickable": "true" if e.get("clickable") else "false",
        "focusable": "true" if e.get("focusable", True) else "false",
        "password": "true" if e.get("password") else "false",
        "bounds": f"[{x1},{y1}][{x2},{y2}]",
    }
    a = " ".join(f'{k}="{v}"' for k, v in attrs.items())
    return f"    <node {a}/>"


def build(case: dict, outdir: pathlib.Path) -> None:
    nodes = "\n".join(node_xml(i, e) for i, e in enumerate(case["elements"]))
    xml = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
           f'<hierarchy rotation="0" density="{DENSITY}">\n'
           f'  <node index="0" class="android.widget.FrameLayout" '
           f'bounds="[0,0][1080,2160]">\n{nodes}\n  </node>\n</hierarchy>\n')
    (outdir / f"{case['name']}.xml").write_text(xml)
    gt = []
    for e in case["elements"]:
        for w in e.get("defects", []):
            gt.append({"element": ident(e), "wcag": w,
                       "class": "static" if w in STATIC else "judgment"})
    (outdir / f"{case['name']}.expected.json").write_text(
        json.dumps({"name": case["name"], "ground_truth": gt}, indent=2))


CASES = [
    {
        "name": "checkout",
        "elements": [
            {"cls": "TextView", "text": "Checkout", "bounds": [60, 120, 700, 190]},
            {"cls": "EditText", "rid": "cardNumber", "clickable": True,
             "bounds": [60, 300, 1020, 410], "defects": ["3.3.2"]},
            {"cls": "EditText", "rid": "expiry", "clickable": True,
             "bounds": [60, 450, 1020, 560], "defects": ["3.3.2"]},
            {"cls": "ImageButton", "rid": "scanCard", "clickable": True,
             "bounds": [930, 470, 1010, 540], "defects": ["4.1.2", "2.5.8"]},
            {"cls": "TextView", "text": "Total: $42.00", "bounds": [60, 620, 1020, 690]},
            # label present but vague: heuristic passes it, a real model should FAIL it
            {"cls": "Button", "rid": "payBtn", "desc": "click here", "clickable": True,
             "bounds": [60, 780, 1020, 900], "defects": ["2.4.6", "1.1.1"]},
            # visually first, but last in tree -> focus-order defect
            {"cls": "TextView", "text": "Enter payment details", "bounds": [60, 230, 1020, 280],
             "defects": ["2.4.3"]},
        ],
    },
    {
        "name": "settings",
        "elements": [
            {"cls": "ImageButton", "rid": "back", "clickable": True,
             "bounds": [40, 90, 110, 160], "defects": ["4.1.2"]},
            {"cls": "TextView", "text": "Settings", "bounds": [140, 90, 700, 160]},
            {"cls": "ImageView", "rid": "avatar", "desc": "ic_profile_v2.png",
             "bounds": [60, 220, 220, 380], "defects": ["2.4.6"]},
            {"cls": "TextView", "text": "Notifications", "bounds": [60, 440, 700, 510]},
            {"cls": "Switch", "rid": "notifToggle", "clickable": True,
             "bounds": [960, 445, 1020, 505], "defects": ["4.1.2", "2.5.8"]},
            {"cls": "TextView", "text": "Dark mode", "bounds": [60, 580, 700, 650]},
            {"cls": "Switch", "rid": "darkToggle", "desc": "on", "clickable": True,
             "bounds": [940, 580, 1020, 660], "defects": ["2.4.6"]},
        ],
    },
    {
        "name": "player",
        "elements": [
            {"cls": "TextView", "text": "Now Playing", "bounds": [60, 120, 700, 190]},
            {"cls": "ImageView", "rid": "art", "desc": "cover_720.jpg",
             "bounds": [60, 240, 1020, 1000], "defects": ["2.4.6"]},
            {"cls": "ImageButton", "rid": "prev", "clickable": True,
             "bounds": [120, 1100, 240, 1220]},
            {"cls": "ImageButton", "rid": "playPause", "desc": "icon", "clickable": True,
             "bounds": [480, 1080, 640, 1240], "defects": ["2.4.6"]},
            {"cls": "ImageButton", "rid": "next", "clickable": True,
             "bounds": [840, 1100, 960, 1220], "defects": ["4.1.2"]},
            {"cls": "SeekBar", "rid": "scrubber", "clickable": True,
             "bounds": [60, 1300, 1020, 1330], "defects": ["2.5.8"]},
        ],
    },
]

if __name__ == "__main__":
    out = pathlib.Path(__file__).parent / "corpus"
    out.mkdir(exist_ok=True)
    for c in CASES:
        build(c, out)
    # include the existing login screen with a hand-labeled ground truth
    login_gt = {
        "name": "login",
        "ground_truth": [
            {"element": "emailField", "wcag": "3.3.2", "class": "static"},
            {"element": "emailField", "wcag": "2.5.8", "class": "static"},
            {"element": "passwordField", "wcag": "3.3.2", "class": "static"},
            {"element": "passwordField", "wcag": "2.5.8", "class": "static"},
            {"element": "togglePwd", "wcag": "4.1.2", "class": "static"},
            {"element": "togglePwd", "wcag": "2.5.8", "class": "static"},
            {"element": "forgot", "wcag": "2.5.8", "class": "static"},
            {"element": "signInBtn", "wcag": "2.4.6", "class": "judgment"},
            {"element": "signInBtn", "wcag": "1.1.1", "class": "judgment"},
            {"element": "brand", "wcag": "2.4.6", "class": "judgment"},
            {"element": "signInBtn", "wcag": "2.4.3", "class": "judgment"},
        ],
    }
    (out / "login.expected.json").write_text(json.dumps(login_gt, indent=2))
    import shutil
    shutil.copy(pathlib.Path(__file__).parent.parent / "examples" / "sample_login_dump.xml",
                out / "login.xml")
    print("corpus built:", ", ".join(sorted(p.name for p in out.glob("*.xml"))))
