"""Accessibility-tree model.

A screen reader does not read pixels, it reads the accessibility tree. On
Android that tree is what ``uiautomator dump`` emits and what Appium and
Espresso query. This module parses that tree into typed nodes so the rest of
the engine can reason about it the way an assistive technology would.

Density: sizes are judged in density-independent pixels (dp). A raw
``uiautomator dump`` does not record screen density, so ``a11yjourney
capture`` writes it into the file. For dumps captured another way, pass
``density=`` (dpi / 160, for example 2.625 for a 420 dpi phone).
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

_EDITABLE = ("EditText", "AutoCompleteTextView", "MultiAutoCompleteTextView")
_BOUNDS = re.compile(r"\[(-?\d+),(-?\d+)]\[(-?\d+),(-?\d+)]")


@dataclass(frozen=True)
class Node:
    """A single element in the accessibility tree."""

    cls: str = ""
    text: str = ""
    desc: str = ""
    hint: str = ""
    inner_text: str = ""  # text of descendants, which TalkBack reads for unlabeled containers
    rid: str = ""
    clickable: bool = False
    focusable: bool = False
    password: bool = False
    enabled: bool = True
    scrollable: bool = False
    in_scroll: bool = False
    bounds: tuple[int, int, int, int] = (0, 0, 0, 0)
    w_dp: float = 0.0
    h_dp: float = 0.0
    cx: int = 0
    cy: int = 0

    @property
    def name(self) -> str:
        """The element's own accessible name (content description, then text)."""
        return self.desc or self.text

    @property
    def announced(self) -> str:
        """What a screen reader would say for this element when it gets focus:
        its own name, a field's hint, or else the text of its descendants."""
        if self.editable:
            return self.desc or self.hint  # typed text is user data, not a label
        return self.name or self.inner_text

    @property
    def ident(self) -> str:
        return self.rid or self.name or self.cls or "unknown"

    @property
    def actionable(self) -> bool:
        return self.clickable or self.cls in ("EditText", "Button", "ImageButton")

    @property
    def editable(self) -> bool:
        return self.cls in _EDITABLE

    @property
    def visible(self) -> bool:
        x1, y1, x2, y2 = self.bounds
        return x2 > x1 and y2 > y1


@dataclass(frozen=True)
class Screen:
    """A captured screen: its nodes plus device density and size (px)."""

    nodes: tuple[Node, ...] = field(default_factory=tuple)
    density: float = 1.0
    density_known: bool = True
    width: int = 0
    height: int = 0

    def focus_order(self) -> list[Node]:
        """Nodes in the order a screen reader traverses them (tree order)."""
        return [n for n in self.nodes if n.focusable]

    def visual_order(self) -> list[Node]:
        """The same focusable nodes in visual reading order (top-to-bottom)."""
        return sorted(self.focus_order(), key=lambda n: (n.cy, n.cx))


def _parse_bounds(raw: str) -> tuple[int, int, int, int]:
    m = _BOUNDS.findall(raw or "")
    if not m:
        return (0, 0, 0, 0)
    x1, y1, x2, y2 = (int(v) for v in m[0])
    return (x1, y1, x2, y2)


def _short(value: str) -> str:
    return value.split(".")[-1]


def parse(xml_text: str, density: float | None = None) -> Screen:
    """Parse ``uiautomator dump`` XML text into a :class:`Screen`."""
    root = ET.fromstring(xml_text)
    attr = root.get("density")
    if attr:
        dens, known = float(attr) or 1.0, True
    elif density:
        dens, known = density, True
    else:
        dens, known = 1.0, False

    nodes: list[Node] = []
    width = height = 0

    def inner(el: ET.Element) -> str:
        parts = []
        for d in el.iter("node"):
            if d is el:
                continue
            if _short(d.get("class", "") or "") in _EDITABLE:  # typed text is user data
                parts.append(d.get("content-desc") or d.get("hint") or "")
            else:
                parts.append(d.get("content-desc") or d.get("text") or "")
        return " ".join(p for p in parts if p)[:200]

    def walk(el: ET.Element, in_scroll: bool) -> None:
        nonlocal width, height
        for n in el.findall("node"):
            x1, y1, x2, y2 = _parse_bounds(n.get("bounds", ""))
            width, height = max(width, x2), max(height, y2)
            scrollable = n.get("scrollable") == "true"
            nodes.append(
                Node(
                    cls=_short(n.get("class", "") or ""),
                    text=n.get("text", "") or "",
                    desc=n.get("content-desc", "") or "",
                    hint=n.get("hint", "") or "",
                    inner_text=inner(n),
                    rid=(n.get("resource-id", "") or "").split("/")[-1],
                    clickable=n.get("clickable") == "true",
                    focusable=n.get("focusable") == "true",
                    password=n.get("password") == "true",
                    enabled=n.get("enabled", "true") != "false",
                    scrollable=scrollable,
                    in_scroll=in_scroll,
                    bounds=(x1, y1, x2, y2),
                    w_dp=(x2 - x1) / dens,
                    h_dp=(y2 - y1) / dens,
                    cx=(x1 + x2) // 2,
                    cy=(y1 + y2) // 2,
                )
            )
            walk(n, in_scroll or scrollable)

    walk(root, False)
    return Screen(nodes=tuple(nodes), density=dens, density_known=known,
                  width=width, height=height)


def load(path: str, density: float | None = None) -> Screen:
    """Load a ``uiautomator dump`` XML file into a :class:`Screen`."""
    with open(path, encoding="utf-8") as fh:
        return parse(fh.read(), density)
