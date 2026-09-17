"""The check engine: structural, semantic, and journey-level rules."""
from __future__ import annotations

from dataclasses import dataclass

from .judge import HeuristicJudge, Judge
from .model import Screen
from .wcag import Severity

MIN_TARGET_DP = 48


@dataclass(frozen=True)
class Finding:
    kind: str  # STRUCTURAL | SEMANTIC | JOURNEY
    wcag: str
    severity: Severity
    element: str
    message: str


def _structural(screen: Screen) -> list[Finding]:
    out: list[Finding] = []
    for n in screen.nodes:
        if n.actionable and not n.name and n.cls != "EditText":
            out.append(Finding("STRUCTURAL", "4.1.2", Severity.SERIOUS, n.ident,
                               f"{n.cls} is actionable but has no accessible name."))
        if n.cls == "EditText" and not n.name:
            out.append(Finding("STRUCTURAL", "3.3.2", Severity.SERIOUS, n.ident,
                               "Input field has no programmatic label."))
        if n.actionable and (n.w_dp < MIN_TARGET_DP or n.h_dp < MIN_TARGET_DP):
            out.append(Finding("STRUCTURAL", "2.5.8", Severity.MODERATE, n.ident,
                               f"Target {n.w_dp:.0f}x{n.h_dp:.0f}dp is below "
                               f"the {MIN_TARGET_DP}dp minimum."))
    return out


def _semantic(screen: Screen, judge: Judge) -> list[Finding]:
    out: list[Finding] = []
    context = [n.name for n in screen.nodes if n.name][:12]

    for n in screen.nodes:
        if n.name and not judge.label_meaningful(n, context):
            out.append(Finding("SEMANTIC", "2.4.6", Severity.SERIOUS, n.ident,
                               f"Label {n.name!r} is present but not meaningful. "
                               "Static scanners score this as a pass."))

    focus, visual = screen.focus_order(), screen.visual_order()
    for i, (a, b) in enumerate(zip(focus, visual)):
        if a is not b:
            out.append(Finding("SEMANTIC", "2.4.3", Severity.SERIOUS, a.ident,
                               f"Focus order is illogical near position {i + 1}: "
                               f"{a.ident!r} is reached before the visually earlier {b.ident!r}."))
            break
    return out


def _journey(screen: Screen, judge: Judge) -> list[Finding]:
    out: list[Finding] = []
    primaries = [n for n in screen.nodes
                 if n.cls == "Button" or "sign" in n.rid.lower() or "submit" in n.rid.lower()]
    for p in primaries:
        if not judge.label_meaningful(p, []):
            out.append(Finding("JOURNEY", "1.1.1", Severity.CRITICAL, p.ident,
                               "Primary action is not identifiable by a screen-reader user; "
                               "the task cannot be completed even if every element looks valid."))
    return out


def run(screen: Screen, judge: Judge | None = None) -> list[Finding]:
    """Run every check against a screen and return findings."""
    j = judge or HeuristicJudge()
    return _structural(screen) + _semantic(screen, j) + _journey(screen, j)
