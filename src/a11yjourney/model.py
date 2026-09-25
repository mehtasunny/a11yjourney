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
from dataclasses import dataclass, field, replace

_EDITABLE = ("EditText", "AutoCompleteTextView", "MultiAutoCompleteTextView")
_CONTROLS = ("EditText", "Button", "ImageButton")
# Classes Jetpack Compose reports on an empty child node to carry the role of its
# clickable parent. The parent is the element TalkBack focuses.
_ROLES = ("Button", "ImageButton", "RadioButton", "CheckBox", "Switch", "ToggleButton",
          "CompoundButton", "SeekBar", "Spinner")
_GENERIC = ("View", "ViewGroup", "FrameLayout", "LinearLayout", "RelativeLayout",
            "ConstraintLayout")
_SCROLLERS = ("ScrollView", "HorizontalScrollView", "NestedScrollView", "RecyclerView",
              "ListView", "GridView", "ViewPager")
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
    clipped: bool = False  # cut off by the edge of the screen or a scrolling container
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
            # a field's label: its description, its hint, or a label drawn inside it
            # (Jetpack Compose text fields expose the label as a child). Typed text is
            # user data, not a label, and is never used.
            return self.desc or self.hint or self.inner_text
        return self.name or self.inner_text

    @property
    def ident(self) -> str:
        return self.rid or self.name or self.announced[:60] or self.cls or "unknown"

    @property
    def actionable(self) -> bool:
        """Something a user can activate: clickable, or a focusable control."""
        return self.clickable or (self.focusable and self.cls in _CONTROLS)

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
        """The same focusable nodes in visual reading order: rows top to bottom, and
        left to right within a row. Elements are in the same row when they overlap
        vertically by more than half the shorter one's height."""
        rows: list[list[Node]] = []
        for n in sorted(self.focus_order(), key=lambda n: (n.bounds[1], n.bounds[0])):
            row = rows[-1] if rows else None
            if row is not None and _same_row(row[0], n):
                row.append(n)
            else:
                rows.append([n])
        return [n for row in rows for n in sorted(row, key=lambda n: n.bounds[0])]


def _same_row(a: Node, b: Node) -> bool:
    top, bottom = max(a.bounds[1], b.bounds[1]), min(a.bounds[3], b.bounds[3])
    shorter = min(a.bounds[3] - a.bounds[1], b.bounds[3] - b.bounds[1]) or 1
    return (bottom - top) / shorter > 0.5


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

    def role_leaf(el: ET.Element, parent: ET.Element) -> bool:
        interactive = parent.get("clickable") == "true" or parent.get("focusable") == "true"
        return (interactive
                and _short(el.get("class", "") or "") in _ROLES
                and el.get("clickable") != "true" and el.get("focusable") != "true"
                and not (el.get("text") or el.get("content-desc"))
                and el.find("node") is None)

    Box = tuple[int, int, int, int]

    def walk(el: ET.Element, scroll: Box | None) -> None:
        nonlocal width, height
        kids = el.findall("node")
        for n in kids:
            if role_leaf(n, el):
                continue
            x1, y1, x2, y2 = _parse_bounds(n.get("bounds", ""))
            width, height = max(width, x2), max(height, y2)
            cls = _short(n.get("class", "") or "")
            leaf = next((c for c in n.findall("node") if role_leaf(c, n)), None)
            if leaf is not None and cls in _GENERIC:
                cls = _short(leaf.get("class", "") or "")
            scrollable = n.get("scrollable") == "true" or cls in _SCROLLERS
            clipped = scroll is not None and (y1 <= scroll[1] or y2 >= scroll[3])
            nodes.append(
                Node(
                    cls=cls,
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
                    in_scroll=scroll is not None,
                    clipped=clipped,
                    bounds=(x1, y1, x2, y2),
                    w_dp=(x2 - x1) / dens,
                    h_dp=(y2 - y1) / dens,
                    cx=(x1 + x2) // 2,
                    cy=(y1 + y2) // 2,
                )
            )
            walk(n, (x1, y1, x2, y2) if scrollable else scroll)

    walk(root, None)
    # anything touching the bottom of the screen is probably cut off there too
    final = tuple(replace(n, clipped=True) if n.bounds[3] >= height and height else n
                  for n in nodes)
    return Screen(nodes=final, density=dens, density_known=known,
                  width=width, height=height)


def load(path: str, density: float | None = None) -> Screen:
    """Load a ``uiautomator dump`` XML file into a :class:`Screen`."""
    with open(path, encoding="utf-8") as fh:
        return parse(fh.read(), density)
