"""Color contrast checks measured from a screenshot.

WCAG 1.4.3 (text) and 1.4.11 (icons and other non-text controls) are about
what is drawn on screen, so the accessibility tree alone cannot answer them.
Given a screenshot captured with the tree, this module estimates each
element's foreground and background colors from its pixels and computes the
WCAG contrast ratio.

It is an estimate, and every result says so. The background is the dominant
color in the element's bounds; the foreground is the significant color with
the strongest contrast against it. Elements on gradients or photos (no
dominant background) are skipped rather than guessed. Disabled controls are
skipped because WCAG exempts inactive components.
"""
from __future__ import annotations

from .findings import VISUAL, Finding
from .imaging import RGB, Image, contrast
from .model import Node, Screen
from .wcag import Severity

TEXT_AA = 4.5
LARGE_TEXT_AA = 3.0
NON_TEXT_AA = 3.0

_MIN_PIXELS = 64
_BG_SHARE = 0.40  # background must cover this share of the bounds
_FG_SHARE = 0.005  # a foreground color must cover at least this share
_ICON_MAX_DP = 96.0


def _hex(c: RGB) -> str:
    return "#{:02X}{:02X}{:02X}".format(*c)


def estimate(pixels: list[RGB]) -> tuple[RGB, RGB, float] | None:
    """Return (foreground, background, ratio), or None if it cannot be judged."""
    if len(pixels) < _MIN_PIXELS:
        return None
    buckets: dict[tuple[int, int, int], list[int]] = {}
    for r, g, b in pixels:
        acc = buckets.setdefault((r >> 3, g >> 3, b >> 3), [0, 0, 0, 0])
        acc[0] += 1
        acc[1] += r
        acc[2] += g
        acc[3] += b
    colors = sorted(
        ((n, (sr // n, sg // n, sb // n)) for n, sr, sg, sb in buckets.values()),
        reverse=True,
    )
    total = len(pixels)
    bg_count, bg = colors[0]
    if bg_count / total < _BG_SHARE:
        return None
    floor = max(6, int(total * _FG_SHARE))
    candidates = [c for n, c in colors[1:] if n >= floor]
    if not candidates:
        return None
    fg = max(candidates, key=lambda c: contrast(c, bg))
    return fg, bg, contrast(fg, bg)


def _fits(screen: Screen, image: Image) -> bool:
    return screen.width <= image.width + 2 and screen.height <= image.height + 2


def _is_icon_control(n: Node) -> bool:
    return (n.cls in ("ImageButton", "ImageView") and n.clickable and not n.text
            and 0 < n.w_dp <= _ICON_MAX_DP and 0 < n.h_dp <= _ICON_MAX_DP)


def check(screen: Screen, image: Image) -> tuple[list[Finding], list[str]]:
    """Run contrast checks. Returns findings plus notes about skipped work."""
    notes: list[str] = []
    if not _fits(screen, image):
        notes.append(
            f"screenshot is {image.width}x{image.height}px but the tree spans "
            f"{screen.width}x{screen.height}px; contrast checks skipped "
            "(capture both at the same moment, same orientation)")
        return [], notes

    out: list[Finding] = []
    skipped = 0
    for n in screen.nodes:
        if not n.enabled or not n.visible or n.password:
            continue
        is_text = bool(n.text.strip())
        is_icon = _is_icon_control(n)
        if not (is_text or is_icon):
            continue
        result = estimate(image.region(*n.bounds))
        if result is None:
            skipped += 1
            continue
        fg, bg, ratio = result
        colors = f"{_hex(fg)} on {_hex(bg)}"
        if is_text and ratio < LARGE_TEXT_AA:
            out.append(Finding(VISUAL, "1.4.3", Severity.SERIOUS, n.ident,
                               f"Text contrast is about {ratio:.1f}:1 ({colors}); "
                               f"WCAG AA needs {TEXT_AA}:1, or {LARGE_TEXT_AA}:1 for large text.",
                               review=True))
        elif is_text and ratio < TEXT_AA:
            out.append(Finding(VISUAL, "1.4.3", Severity.MODERATE, n.ident,
                               f"Text contrast is about {ratio:.1f}:1 ({colors}); this passes "
                               "only if the text is large-scale (WCAG's 18pt, or 14pt bold).",
                               review=True))
        elif is_icon and ratio < NON_TEXT_AA:
            out.append(Finding(VISUAL, "1.4.11", Severity.SERIOUS, n.ident,
                               f"Icon contrast is about {ratio:.1f}:1 ({colors}); "
                               f"controls need {NON_TEXT_AA}:1 against their background.",
                               review=True))
    if skipped:
        notes.append(f"contrast: {skipped} element(s) skipped (no uniform background "
                     "or too small to measure)")
    return out, notes
