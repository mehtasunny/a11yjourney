"""A typed registry of the success criteria this engine maps findings to.

Every finding is traceable to a specific, citable criterion, including the
WCAG version that introduced it and its conformance level. That matters in
practice: U.S. rules adopted in 2024 (ADA Title II, HHS Section 504) require
WCAG **2.1** Level AA, so a finding against a WCAG 2.2-only or Level AAA
criterion is useful advice but not a conformance failure under those rules.
The :class:`Profile` makes that distinction explicit in every report.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    CRITICAL = "critical"
    SERIOUS = "serious"
    MODERATE = "moderate"

    @property
    def sarif_level(self) -> str:
        return {"critical": "error", "serious": "error", "moderate": "warning"}[self.value]


_LEVEL_RANK = {"A": 1, "AA": 2, "AAA": 3}


@dataclass(frozen=True)
class Criterion:
    id: str
    name: str
    url: str
    level: str  # "A" | "AA" | "AAA" | "platform"
    since: str  # WCAG version that introduced it: "2.0" | "2.1" | "2.2"; "" for platform

    @property
    def label(self) -> str:
        if self.level == "platform":
            return self.name
        added = f", added in WCAG {self.since}" if self.since not in ("", "2.0") else ""
        return f"WCAG {self.id} {self.name}, Level {self.level}{added}"


@dataclass(frozen=True)
class Profile:
    """The conformance target a report is judged against."""

    key: str
    version: str
    level: str

    @property
    def title(self) -> str:
        return f"WCAG {self.version} Level {self.level}"

    def covers(self, c: Criterion) -> bool:
        """True when a failure of ``c`` is a conformance failure under this profile."""
        if c.level not in _LEVEL_RANK or not c.since:
            return False
        return _vkey(c.since) <= _vkey(self.version) and (
            _LEVEL_RANK[c.level] <= _LEVEL_RANK[self.level]
        )


def _vkey(v: str) -> tuple[int, ...]:
    return tuple(int(p) for p in v.split("."))


PROFILES: dict[str, Profile] = {
    "wcag21-aa": Profile("wcag21-aa", "2.1", "AA"),
    "wcag22-aa": Profile("wcag22-aa", "2.2", "AA"),
}
DEFAULT_PROFILE = PROFILES["wcag21-aa"]

_U = "https://www.w3.org/WAI/WCAG22/Understanding/"


def _c(cid: str, name: str, slug: str, level: str, since: str) -> Criterion:
    return Criterion(cid, name, _U + slug + ".html", level, since)


CRITERIA: dict[str, Criterion] = {
    c.id: c
    for c in (
        _c("1.1.1", "Non-text Content", "non-text-content", "A", "2.0"),
        _c("1.3.1", "Info and Relationships", "info-and-relationships", "A", "2.0"),
        _c("1.3.2", "Meaningful Sequence", "meaningful-sequence", "A", "2.0"),
        _c("1.4.3", "Contrast (Minimum)", "contrast-minimum", "AA", "2.0"),
        _c("1.4.4", "Resize Text", "resize-text", "AA", "2.0"),
        _c("1.4.11", "Non-text Contrast", "non-text-contrast", "AA", "2.1"),
        _c("2.4.3", "Focus Order", "focus-order", "A", "2.0"),
        _c("2.4.6", "Headings and Labels", "headings-and-labels", "AA", "2.0"),
        _c("2.5.5", "Target Size (Enhanced)", "target-size-enhanced", "AAA", "2.1"),
        _c("2.5.8", "Target Size (Minimum)", "target-size-minimum", "AA", "2.2"),
        _c("3.3.2", "Labels or Instructions", "labels-or-instructions", "A", "2.0"),
        _c("4.1.2", "Name, Role, Value", "name-role-value", "A", "2.0"),
    )
}

# Platform guidance that is not a WCAG criterion but matters to real users.
CRITERIA["android-touch-target"] = Criterion(
    "android-touch-target",
    "Android touch target guidance (48dp)",
    "https://support.google.com/accessibility/android/answer/7101858",
    "platform",
    "",
)


def criterion(cid: str) -> Criterion:
    return CRITERIA.get(cid, Criterion(cid, "Unknown", _U, "platform", ""))
