"""Pattern checks that mirror common Accessibility Test Framework (ATF) checks.

Google's ATF runs inside instrumented tests and Accessibility Scanner. These are the
equivalents that can be judged from a captured accessibility tree, so the same classes
of problems are reported for any installed app, in the same report as everything else:

* several controls announced with the same label (ATF DuplicateSpeakableTextCheck)
* a label that only says "click here", "learn more" and the like (LinkPurposeUnclearCheck)
* a label that repeats the control's role, such as "Submit button" (RedundantDescriptionCheck)
* nested clickable elements with identical bounds (DuplicateClickableBoundsCheck)
* an editable field with a content description (EditableContentDescCheck)
"""
from __future__ import annotations

import re
from collections import defaultdict

from .findings import SEMANTIC, STRUCTURAL, Finding
from .model import Node, Screen
from .wcag import Severity

_UNCLEAR = {
    "click here", "tap here", "here", "click", "tap", "learn more", "read more", "more",
    "more info", "more information", "details", "link", "this link", "see more", "info",
}

_ROLE_WORDS = {
    "Button": ("button", "btn"),
    "ImageButton": ("button", "btn", "icon", "image"),
    "CheckBox": ("checkbox", "check box"),
    "Switch": ("switch", "toggle"),
    "ToggleButton": ("toggle", "button"),
    "RadioButton": ("radio button", "radio"),
    "ImageView": ("image", "icon", "picture", "photo"),
}


def _norm(text: str) -> str:
    return re.sub(r"[\s.!:,]+", " ", text).strip().lower()


def _nested(a: Node, b: Node) -> bool:
    ab, bb = a.bounds, b.bounds
    inside = ab[0] <= bb[0] and ab[1] <= bb[1] and ab[2] >= bb[2] and ab[3] >= bb[3]
    outside = bb[0] <= ab[0] and bb[1] <= ab[1] and bb[2] >= ab[2] and bb[3] >= ab[3]
    return inside or outside


def check(screen: Screen) -> list[Finding]:
    out: list[Finding] = []
    targets = [n for n in screen.nodes if n.actionable and n.visible and n.enabled]

    # 1. duplicate labels on different controls
    groups: dict[str, list[Node]] = defaultdict(list)
    for n in targets:
        label = _norm(n.announced)
        if label and not n.editable:
            groups[label].append(n)
    for nodes in groups.values():
        distinct = [n for i, n in enumerate(nodes)
                    if not any(_nested(n, m) for m in nodes[:i])]
        if len(distinct) >= 2:
            out.append(Finding(
                SEMANTIC, "2.4.6", Severity.MODERATE, distinct[0].announced[:60],
                f"{len(distinct)} controls are announced as {distinct[0].announced!r}. "
                "If they do different things, screen-reader users cannot tell them apart.",
                review=True))

    # 2. purpose that only makes sense visually
    for n in targets:
        label = _norm(n.announced)
        if label in _UNCLEAR:
            link_like = n.cls in ("TextView", "View") and n.clickable
            out.append(Finding(
                SEMANTIC, "2.4.4" if link_like else "2.4.6", Severity.MODERATE, n.ident,
                f"{n.announced!r} does not say where it goes or what it does when heard "
                "out of context, for example in a screen reader's list of links.",
                review=True))

    # 3. label repeats the role the screen reader already announces
    for n in screen.nodes:
        words = _ROLE_WORDS.get(n.cls)
        desc = _norm(n.desc)
        if words and desc and any(re.search(rf"\b{re.escape(w)}\b", desc) for w in words):
            out.append(Finding(
                STRUCTURAL, "android-redundant-role", Severity.MODERATE, n.ident,
                f"Label {n.desc!r} repeats the role; TalkBack will say it twice "
                f"(\"{n.desc}, {n.cls}\")."))

    # 4. nested clickable elements with identical bounds
    clickable = [n for n in screen.nodes if n.clickable and n.visible]
    seen: set[tuple[int, int, int, int]] = set()
    for i, a in enumerate(clickable):
        for b in clickable[i + 1:]:
            if a.bounds == b.bounds and a.bounds not in seen:
                seen.add(a.bounds)
                out.append(Finding(
                    STRUCTURAL, "android-duplicate-clickable", Severity.MODERATE, b.ident,
                    "Two nested clickable elements cover exactly the same area, so "
                    "screen-reader and switch users may land on the same control twice."))

    # 5. content description on an editable field hides what the user typed
    for n in screen.nodes:
        if n.editable and n.desc:
            out.append(Finding(
                STRUCTURAL, "android-editable-description", Severity.MODERATE, n.ident,
                f"Editable field has the content description {n.desc!r}, which replaces "
                "what the user typed when a screen reader reads it. Use a label or hint "
                "instead."))
    return out
