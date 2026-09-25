"""The check engine: structural, visual, resize, semantic, and journey rules."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from . import contrast, resize
from .findings import JOURNEY, SEMANTIC, STRUCTURAL, Finding
from .imaging import Image
from .judge import HeuristicJudge, Judge
from .model import Node, Screen
from .wcag import Severity

__all__ = ["Audit", "Finding", "audit", "run"]

WCAG22_MIN_DP = 24  # 2.5.8 Target Size (Minimum), WCAG 2.2 AA
WCAG21_AAA_DP = 44  # 2.5.5 Target Size, WCAG 2.1 AAA
ANDROID_MIN_DP = 48  # Android accessibility guidance


@dataclass(frozen=True)
class Audit:
    """Everything one run produced: findings plus notes about what was skipped."""

    findings: list[Finding] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _contains(outer: Node, inner: Node) -> bool:
    o, i = outer.bounds, inner.bounds
    return o[0] <= i[0] and o[1] <= i[1] and o[2] >= i[2] and o[3] >= i[3]


def _dist_to_rect(px: float, py: float, b: tuple[int, int, int, int]) -> float:
    dx = max(b[0] - px, 0.0, px - b[2])
    dy = max(b[1] - py, 0.0, py - b[3])
    return math.hypot(dx, dy)


def _undersized(n: Node) -> bool:
    return n.w_dp < WCAG22_MIN_DP or n.h_dp < WCAG22_MIN_DP


def _spacing_ok(n: Node, targets: list[Node], density: float) -> bool:
    """WCAG 2.5.8 spacing exception: a 24dp circle centered on the target must not
    intersect another target, or the 24dp circle of another undersized target."""
    radius_px = (WCAG22_MIN_DP / 2) * density
    for o in targets:
        if o is n or _contains(n, o) or (_contains(o, n) and not o.editable):
            continue
        if _undersized(o):
            if math.hypot(n.cx - o.cx, n.cy - o.cy) < 2 * radius_px:
                return False
        elif _dist_to_rect(n.cx, n.cy, o.bounds) < radius_px:
            return False
    return True


def _target_size(n: Node, targets: list[Node], density: float) -> Finding | None:
    w, h = n.w_dp, n.h_dp
    size = f"{w:.0f}x{h:.0f}dp"
    if _undersized(n) and not _spacing_ok(n, targets, density):
        return Finding(STRUCTURAL, "2.5.8", Severity.SERIOUS, n.ident,
                       f"Target is {size}, under {WCAG22_MIN_DP}dp, and too close to "
                       "other targets for the spacing exception.")
    if w < WCAG21_AAA_DP or h < WCAG21_AAA_DP:
        return Finding(STRUCTURAL, "2.5.5", Severity.MODERATE, n.ident,
                       f"Target is {size}; below {WCAG21_AAA_DP}dp it is hard to hit "
                       f"for people with tremors or limited dexterity (Android guidance "
                       f"is {ANDROID_MIN_DP}dp).")
    if w < ANDROID_MIN_DP or h < ANDROID_MIN_DP:
        return Finding(STRUCTURAL, "android-touch-target", Severity.MODERATE, n.ident,
                       f"Target is {size}, under the {ANDROID_MIN_DP}dp Android minimum.")
    return None


def _structural(screen: Screen, notes: list[str]) -> list[Finding]:
    out: list[Finding] = []
    targets = [n for n in screen.nodes if n.actionable and n.visible]
    for n in screen.nodes:
        if n.actionable and not n.announced and not n.editable:
            out.append(Finding(STRUCTURAL, "4.1.2", Severity.SERIOUS, n.ident,
                               f"{n.cls} is actionable but has no accessible name."))
        if n.editable and not n.announced:
            out.append(Finding(STRUCTURAL, "3.3.2", Severity.SERIOUS, n.ident,
                               "Input field has no programmatic label."))
    if not screen.density_known:
        notes.append("target size: screen density unknown, so sizes in dp cannot be "
                     "computed; pass --density or capture with `a11yjourney capture`")
        return out
    clipped = 0
    for n in targets:
        if n.clipped:
            clipped += 1
            continue
        f = _target_size(n, targets, screen.density)
        if f:
            out.append(f)
    if clipped:
        notes.append(f"target size: {clipped} element(s) cut off at the edge of the screen or "
                     "a scrolling area were not measured; scroll and capture again to check them")
    return out


def _semantic(screen: Screen, judge: Judge) -> list[Finding]:
    out: list[Finding] = []
    # Text typed into a field is user data, not a label: never judge or share it.
    context = [n.name for n in screen.nodes if n.name and not n.editable][:12]

    for n in screen.nodes:
        label = (n.desc or n.hint) if n.editable else n.name
        if label and not judge.label_meaningful(n, context):
            out.append(Finding(SEMANTIC, "2.4.6", Severity.SERIOUS, n.ident,
                               f"Label {n.name!r} is present but not meaningful. "
                               "Presence-only scanners score this as a pass."))

    focus, visual = screen.focus_order(), screen.visual_order()
    for i, (a, b) in enumerate(zip(focus, visual, strict=True)):
        if a is not b:
            out.append(Finding(SEMANTIC, "2.4.3", Severity.SERIOUS, a.ident,
                               f"Focus order is illogical near position {i + 1}: "
                               f"{a.ident!r} is reached before the visually earlier "
                               f"{b.ident!r}."))
            break
    return out


def _journey(screen: Screen, judge: Judge) -> list[Finding]:
    out: list[Finding] = []
    primaries = [n for n in screen.nodes
                 if n.cls == "Button" or "sign" in n.rid.lower() or "submit" in n.rid.lower()]
    for p in primaries:
        if not judge.label_meaningful(p, []):
            out.append(Finding(JOURNEY, "1.1.1", Severity.CRITICAL, p.ident,
                               "Primary action is not identifiable by a screen-reader user; "
                               "the task cannot be completed even if every element looks "
                               "valid."))
    return out


def audit(
    screen: Screen,
    judge: Judge | None = None,
    *,
    image: Image | None = None,
    scaled: Screen | None = None,
) -> Audit:
    """Run every check that the inputs allow.

    ``image`` is a screenshot taken with the tree (enables contrast checks).
    ``scaled`` is a capture of the same screen at 200% font scale (enables the
    resize-text check).
    """
    j = judge or HeuristicJudge()
    notes: list[str] = []
    findings = _structural(screen, notes)
    if image is not None:
        f, n = contrast.check(screen, image)
        findings += f
        notes += n
    if scaled is not None:
        f, n = resize.compare(screen, scaled)
        findings += f
        notes += n
    findings += _semantic(screen, j) + _journey(screen, j)
    return Audit(findings, notes)


def run(screen: Screen, judge: Judge | None = None) -> list[Finding]:
    """Run the tree-only checks against a screen and return findings."""
    return audit(screen, judge).findings
