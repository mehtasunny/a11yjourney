"""Keyboard focus order, measured on the device rather than inferred.

``a11yjourney capture --keyboard`` presses Tab on the device repeatedly and records
which element holds focus after each press (``NAME.focus.json``). Tab is how people
using a keyboard, switch access in step mode, and many other assistive devices move
through an app, and it is what WCAG 2.4.3 (Focus Order), 2.1.1 (Keyboard) and 2.1.2
(No Keyboard Trap) are about.

This measures real behavior. What it cannot measure is TalkBack's swipe order, which
Android computes separately; that is still approximated from the tree (see
``checks._semantic``).
"""
from __future__ import annotations

from typing import Any

from .findings import KEYBOARD, Finding
from .model import Node, Screen, _same_row
from .wcag import Severity


def node_key(n: Node) -> str:
    """A stable name for an element across captures (bounds change as screens scroll)."""
    if n.rid:
        # list items share one resource id, so add the label to tell them apart
        return f"id:{n.rid}|{n.announced[:40]}" if n.announced else f"id:{n.rid}"
    if n.announced:
        return f"{n.cls}:{n.announced[:60]}"
    return f"{n.cls}@{n.bounds}"


def focused_node(screen: Screen) -> Node | None:
    """The innermost element that holds input focus, if any."""
    found = [n for n in screen.nodes if n.focused]
    return found[-1] if found else None


def analyze(screen: Screen, trace: dict[str, Any]) -> tuple[list[Finding], list[str]]:
    steps = [s for s in trace.get("steps", []) if s.get("key")]
    notes: list[str] = []
    targets = [n for n in screen.nodes
               if n.actionable and n.visible and n.enabled and not n.clipped]
    if not targets:
        return [], notes
    if not steps:
        return [Finding(KEYBOARD, "2.1.1", Severity.SERIOUS, "screen",
                        "Pressing Tab never moved focus to any element on this screen, so it "
                        "cannot be used with a keyboard or switch device in step mode.",
                        review=True)], notes

    order: list[str] = []
    for s in steps:
        if s["key"] not in order:
            order.append(s["key"])
    wrapped = bool(trace.get("wrapped"))
    stuck = bool(trace.get("stuck"))
    out: list[Finding] = []

    by_key = {node_key(n): n for n in targets}
    if wrapped:
        for key, n in by_key.items():
            if key not in order:
                out.append(Finding(
                    KEYBOARD, "2.1.1", Severity.SERIOUS, n.ident,
                    "Pressing Tab cycles through the screen without ever reaching this "
                    "control, so keyboard and switch users cannot activate it.", review=True))
    elif stuck:
        last = steps[-1]
        out.append(Finding(
            KEYBOARD, "2.1.2", Severity.SERIOUS, last.get("label") or last["key"],
            "Keyboard focus stays on this element when Tab is pressed again, so keyboard "
            "users cannot move past it.", review=True))
    else:
        notes.append(f"keyboard: stopped after {len(steps)} Tab presses before focus "
                     "cycled back to the start; reachability not judged")

    visual = [n for n in screen.visual_order() if node_key(n) in by_key]
    rank = {node_key(n): i for i, n in enumerate(visual)}
    measured = [k for k in order if k in rank]
    if wrapped and measured:
        # a full cycle has no natural start (focus may already have been somewhere when
        # the walk began), so start it at the element that comes first on screen
        start = min(range(len(measured)), key=lambda i: rank[measured[i]])
        measured = measured[start:] + measured[:start]
    for a, b in zip(measured, measured[1:], strict=False):
        na, nb = by_key[a], by_key[b]
        if rank[b] < rank[a] and not _same_row(na, nb) and nb.bounds[3] <= na.bounds[1]:
            out.append(Finding(
                KEYBOARD, "2.4.3", Severity.SERIOUS, nb.ident,
                f"Measured with Tab: focus moves from {na.ident!r} up to {nb.ident!r}, "
                "which sits above it on screen.", review=True))
            break
    notes.append(f"keyboard: measured {len(order)} focus stops with Tab"
                 + (", cycle complete" if wrapped else ""))
    return out, notes
