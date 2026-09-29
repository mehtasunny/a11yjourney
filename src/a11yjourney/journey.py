"""Multi-screen capture: scripted journeys and a cautious explorer.

A single screen rarely tells the whole story. Two ways to cover more of an app:

**Journeys** replay a short script of steps, so the same task (check in, plan a trip,
apply for benefits) is captured the same way every time, in CI or by hand::

    launch com.example.transit/.MainActivity
    capture home
    tap "Plan trip"
    capture planner
    scroll down
    capture planner-2 keyboard
    back

Steps: ``launch COMPONENT|PACKAGE``, ``tap "LABEL"`` (text, content description, or
resource id), ``type "TEXT"`` (test data only), ``key NAME`` (TAB, ENTER, BACK...),
``back``, ``scroll down|up``, ``wait SECONDS``, ``capture NAME [keyboard] [nolarge]``.

**Exploration** starts from the current screen, opens each control once, captures any
new screen it leads to, and comes back. It never types, and it skips controls whose
labels suggest an action with consequences (delete, pay, send, sign out, and so on).
Even so, it taps real controls: use a test device and a test account.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import shlex
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .capture import Adb, CaptureError, capture, dump_tree, read_density
from .model import Node, Screen, parse

RISKY = re.compile(
    r"\b(delete|remove|erase|clear|reset|pay|buy|purchase|order|checkout|check out|"
    r"subscribe|unsubscribe|send|submit|post|publish|share|call|dial|sign ?out|log ?out|"
    r"sign off|confirm|transfer|cancel|uninstall|report|block|donate|book|apply)\b",
    re.IGNORECASE,
)


class JourneyError(RuntimeError):
    pass


@dataclass
class Session:
    """Talks to the device for journeys and exploration."""

    adb: Adb
    out_dir: pathlib.Path
    sleep: Callable[[float], None] = time.sleep
    settle: float = 1.5
    density: float = 0.0
    log: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        if not self.density:
            self.density = read_density(self.adb)

    def screen(self) -> Screen:
        return parse(dump_tree(self.adb, self.density))

    def launch(self, target: str) -> None:
        if "/" in target:
            self.adb(["shell", "am", "start", "-W", "-n", target])
        else:
            self.adb(["shell", "monkey", "-p", target, "-c",
                      "android.intent.category.LAUNCHER", "1"])
        self.sleep(self.settle)

    def tap_node(self, n: Node) -> None:
        self.adb(["shell", "input", "tap", str(n.cx), str(n.cy)])
        self.sleep(self.settle)

    def tap(self, label: str) -> Node:
        n = find(self.screen(), label)
        if n is None:
            raise JourneyError(f'no element labeled "{label}" on the current screen')
        self.tap_node(n)
        return n

    def back(self) -> None:
        self.adb(["shell", "input", "keyevent", "KEYCODE_BACK"])
        self.sleep(self.settle)

    def key(self, name: str) -> None:
        code = name.upper()
        self.adb(["shell", "input", "keyevent",
                  code if code.startswith("KEYCODE_") else f"KEYCODE_{code}"])
        self.sleep(0.3)

    def type_text(self, text: str) -> None:
        # adb's input text needs spaces escaped as %s
        self.adb(["shell", "input", "text", text.replace(" ", "%s")])
        self.sleep(0.3)

    def scroll(self, direction: str) -> None:
        s = self.screen()
        x = s.width // 2 or 540
        top, bottom = int(s.height * 0.3), int(s.height * 0.75)
        start, end = (bottom, top) if direction == "down" else (top, bottom)
        self.adb(["shell", "input", "swipe", str(x), str(start), str(x), str(end), "400"])
        self.sleep(self.settle)

    def capture(self, name: str, keyboard: bool = False, large_text: bool = True) -> str:
        c = capture(self.adb, str(self.out_dir), name, large_text=large_text,
                    keyboard=keyboard, sleep=self.sleep)
        return str(c.tree)


def find(screen: Screen, label: str) -> Node | None:
    """The element whose text, description, resource id, or announced label matches.

    Exact matches win; then case-insensitive; then case-insensitive substring. Among
    equals, a clickable element wins over a plain one.
    """
    want = label.strip()
    nodes = [n for n in screen.nodes if n.visible]

    def names(n: Node) -> list[str]:
        return [v for v in (n.text, n.desc, n.rid, n.announced) if v]

    for test in (
        lambda v: v == want,
        lambda v: v.lower() == want.lower(),
        lambda v: want.lower() in v.lower(),
    ):
        hits = [n for n in nodes if any(test(v) for v in names(n))]
        if hits:
            clickable = [n for n in hits if n.clickable]
            return (clickable or hits)[0]
    return None


def parse_steps(text: str) -> list[list[str]]:
    steps = []
    for raw in text.splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            steps.append(shlex.split(line))
    return steps


def run_journey(session: Session, steps: list[list[str]]) -> list[str]:
    """Run each step in order; return the paths of the trees it captured."""
    captured: list[str] = []
    for n, step in enumerate(steps, 1):
        op, args = step[0].lower(), step[1:]
        try:
            if op == "launch":
                session.launch(args[0])
            elif op == "tap":
                session.tap(" ".join(args))
            elif op == "type":
                session.type_text(" ".join(args))
            elif op == "key":
                session.key(args[0])
            elif op == "back":
                session.back()
            elif op == "scroll":
                session.scroll(args[0] if args else "down")
            elif op == "wait":
                session.sleep(float(args[0]))
            elif op == "capture":
                flags = {a.lower() for a in args[1:]}
                captured.append(session.capture(args[0], keyboard="keyboard" in flags,
                                                large_text="nolarge" not in flags))
            else:
                raise JourneyError(f"unknown step {op!r}")
        except (IndexError, ValueError) as exc:
            raise JourneyError(f"step {n} ({' '.join(step)}): missing or bad argument") from exc
        except (JourneyError, CaptureError) as exc:
            raise JourneyError(f"step {n} ({' '.join(step)}): {exc}") from exc
        session.log.append({"step": n, "do": " ".join(step)})
    (session.out_dir / "journey.json").write_text(
        json.dumps({"steps": session.log, "captures": captured}, indent=2) + "\n")
    return captured


def signature(screen: Screen) -> str:
    """Identifies a screen by its controls and texts, ignoring positions."""
    parts = sorted(f"{n.cls}:{n.announced[:40]}" for n in screen.nodes
                   if (n.actionable or n.text) and n.visible)
    return hashlib.sha1("\n".join(parts).encode()).hexdigest()[:12]


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:30] or "screen"


def _return_home(session: Session, home: str, package: str) -> bool:
    """Go back to the start screen: Back up to twice, then relaunch the app."""
    for _ in range(2):
        session.back()
        if signature(session.screen()) == home:
            return True
    if package:
        session.launch(package)
        return signature(session.screen()) == home
    return False


_STATEFUL = ("Switch", "CheckBox", "ToggleButton", "RadioButton", "SeekBar", "CompoundButton")


def explore(
    session: Session,
    max_screens: int = 8,
    allow_risky: bool = False,
    keyboard: bool = False,
    package: str = "",
) -> dict[str, Any]:
    """Open each control on the current screen once and capture where it leads.

    Only controls inside the app being explored are tapped. If ``package`` is given and
    the screen belongs to another app (a permission prompt or a system settings page),
    that screen is captured but nothing on it is tapped.
    """
    start = session.screen()
    home = signature(start)
    seen = {home}
    captured = [session.capture("screen-00-start", keyboard=keyboard)]
    visits: list[dict[str, Any]] = []
    app = package or start.package
    if package and start.package and start.package != package:
        visits.append({"control": "(start screen)",
                       "result": f"belongs to {start.package}, not {package}; not explored"})
        result = {"start": home, "captures": captured, "visits": visits}
        (session.out_dir / "explore.json").write_text(json.dumps(result, indent=2) + "\n")
        return result
    candidates = [n for n in start.nodes
                  if n.actionable and n.visible and n.enabled and not n.editable
                  and not n.clipped and n.announced
                  and (allow_risky or n.cls not in _STATEFUL)]
    for n in candidates:
        if len(captured) >= max_screens:
            visits.append({"control": n.announced, "result": "stopped: screen limit"})
            break
        if not allow_risky and RISKY.search(n.announced):
            visits.append({"control": n.announced, "result": "skipped: looks consequential"})
            continue
        session.tap_node(n)
        now = session.screen()
        sig = signature(now)
        if app and now.package and now.package != app:
            visits.append({"control": n.announced,
                           "result": f"opened another app ({now.package}); not captured"})
        elif sig == home:
            visits.append({"control": n.announced, "result": "no new screen"})
            continue
        elif sig in seen:
            visits.append({"control": n.announced, "result": "already captured"})
        else:
            seen.add(sig)
            name = f"screen-{len(captured):02d}-{_slug(n.announced)}"
            captured.append(session.capture(name, keyboard=keyboard))
            visits.append({"control": n.announced, "result": f"captured {name}"})
        if not _return_home(session, home, start.package):
            visits.append({"control": n.announced, "result": "could not return; stopped"})
            break
    result = {"start": home, "captures": captured, "visits": visits}
    (session.out_dir / "explore.json").write_text(json.dumps(result, indent=2) + "\n")
    return result
