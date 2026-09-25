"""Resize-text check (WCAG 1.4.4) from two captures of the same screen.

Many people with low vision set Android's font size to the maximum. WCAG
1.4.4 requires text to stay readable, without losing content or function, at
200%. This check compares a capture at the user's normal font scale with one
taken at 2.0 (``a11yjourney capture`` takes both) and reports text that
disappears, collides with other text, runs off the screen, or does not grow
at all, which usually means it is being clipped or truncated.

These are signals from the accessibility tree, not pixels, so each finding is
marked for a person to confirm on the device.
"""
from __future__ import annotations

from collections import Counter

from .findings import RESIZE, Finding
from .model import Node, Screen
from .wcag import Severity

_GREW = 1.10  # a text box counts as having grown if its height grew 10%
_STUCK = 1.05  # at or below this growth, the text probably did not scale
_MIN_GROWING_SHARE = 0.2
_OVERLAP_SHARE = 0.10


def _key(n: Node) -> str:
    return n.rid or f"{n.cls}:{n.text}"


def _text_nodes(screen: Screen) -> dict[str, Node]:
    nodes = [n for n in screen.nodes if n.text.strip() and n.visible]
    counts = Counter(_key(n) for n in nodes)
    return {_key(n): n for n in nodes if counts[_key(n)] == 1}


def _area(b: tuple[int, int, int, int]) -> int:
    return max(0, b[2] - b[0]) * max(0, b[3] - b[1])


def _overlap(a: Node, b: Node) -> float:
    x1, y1 = max(a.bounds[0], b.bounds[0]), max(a.bounds[1], b.bounds[1])
    x2, y2 = min(a.bounds[2], b.bounds[2]), min(a.bounds[3], b.bounds[3])
    inter = _area((x1, y1, x2, y2))
    smaller = min(_area(a.bounds), _area(b.bounds)) or 1
    return inter / smaller


def _height(n: Node) -> int:
    return n.bounds[3] - n.bounds[1]


def _width(n: Node) -> int:
    return n.bounds[2] - n.bounds[0]


def compare(base: Screen, scaled: Screen) -> tuple[list[Finding], list[str]]:
    """Compare a normal capture with a 200% font-scale capture of the same screen."""
    notes: list[str] = []
    if abs(base.width - scaled.width) > 2:
        notes.append("resize: the two captures have different widths (rotation?); skipped")
        return [], notes

    before, after = _text_nodes(base), _text_nodes(scaled)
    matched = [(k, before[k], after[k]) for k in before if k in after]
    if not matched:
        notes.append("resize: no text elements matched between the two captures; skipped")
        return [], notes
    grew = sum(1 for _, b, a in matched if _height(a) > _height(b) * _GREW)
    if grew / len(matched) < _MIN_GROWING_SHARE:
        notes.append("resize: almost no text grew between captures, so the larger font "
                     "scale may not have been applied; skipped")
        return [], notes

    out: list[Finding] = []
    scrolls = any(n.scrollable for n in scaled.nodes)
    for key, b in before.items():
        if key not in after and not b.in_scroll and not scrolls:
            out.append(Finding(RESIZE, "1.4.4", Severity.SERIOUS, b.ident,
                               "Text is no longer on screen at 200% font size and the screen does "
                               "not scroll, so users cannot reach it.", review=True))

    for _, b, a in matched:
        if a.bounds[2] > base.width + 1:
            out.append(Finding(RESIZE, "1.4.4", Severity.SERIOUS, a.ident,
                               "At 200% font size this text runs past the right edge of the "
                               "screen.", review=True))
        elif _height(a) <= _height(b) * _STUCK and _width(a) <= _width(b) * _GREW:
            out.append(Finding(RESIZE, "1.4.4", Severity.MODERATE, a.ident,
                               "Text box did not grow at 200% font size, so the text is likely "
                               "clipped or truncated. Confirm on the device.", review=True))

    seen: set[frozenset[str]] = set()
    for i, (ka, ba, aa) in enumerate(matched):
        for kb, bb, ab in matched[i + 1:]:
            pair = frozenset((ka, kb))
            if pair in seen:
                continue
            if _overlap(ba, bb) < _OVERLAP_SHARE <= _overlap(aa, ab):
                seen.add(pair)
                out.append(Finding(RESIZE, "1.4.4", Severity.SERIOUS, aa.ident,
                                   f"At 200% font size this text overlaps {ab.ident!r}, "
                                   "which it did not do at normal size.", review=True))
    return out, notes
