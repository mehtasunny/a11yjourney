"""Accessibility-tree model.

A screen reader does not read pixels, it reads the accessibility tree. On
Android that tree is what `uiautomator dump` emits and what Appium/Espresso
query. This module parses that tree into typed nodes so the rest of the
engine can reason about it the way an assistive technology would.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

_BOUNDS = re.compile(r"\[(\d+),(\d+)]\[(\d+),(\d+)]")


@dataclass(frozen=True)
class Node:
    """A single element in the accessibility tree."""

    cls: str = ""
    text: str = ""
    desc: str = ""
    rid: str = ""
    clickable: bool = False
    focusable: bool = False
    password: bool = False
    bounds: tuple[int, int, int, int] = (0, 0, 0, 0)
    w_dp: float = 0.0
    h_dp: float = 0.0
    cx: int = 0
    cy: int = 0

    @property
    def name(self) -> str:
        """The accessible name a screen reader would announce."""
        return self.desc or self.text

    @property
    def ident(self) -> str:
        return self.rid or self.name or self.cls or "unknown"

    @property
    def actionable(self) -> bool:
        return self.clickable or self.cls in ("EditText", "Button", "ImageButton")


@dataclass(frozen=True)
class Screen:
    """A captured screen: its nodes plus device density."""

    nodes: tuple[Node, ...] = field(default_factory=tuple)
    density: float = 1.0

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


def load(path: str) -> Screen:
    """Load a `uiautomator dump` XML file into a :class:`Screen`."""
    root = ET.parse(path).getroot()
    density = float(root.get("density", "1.0")) or 1.0
    nodes: list[Node] = []
    for n in root.iter("node"):
        x1, y1, x2, y2 = _parse_bounds(n.get("bounds", ""))
        nodes.append(
            Node(
                cls=(n.get("class", "") or "").split(".")[-1],
                text=n.get("text", "") or "",
                desc=n.get("content-desc", "") or "",
                rid=(n.get("resource-id", "") or "").split("/")[-1],
                clickable=n.get("clickable") == "true",
                focusable=n.get("focusable") == "true",
                password=n.get("password") == "true",
                bounds=(x1, y1, x2, y2),
                w_dp=(x2 - x1) / density,
                h_dp=(y2 - y1) / density,
                cx=(x1 + x2) // 2,
                cy=(y1 + y2) // 2,
            )
        )
    return Screen(nodes=tuple(nodes), density=density)
