"""A small registry of the WCAG success criteria this engine maps to.

Keeping criteria in one typed registry means every finding is traceable to a
specific, citable standard, which is what auditors and compliance teams need.
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


@dataclass(frozen=True)
class Criterion:
    id: str
    name: str
    url: str


_BASE = "https://www.w3.org/WAI/WCAG22/Understanding/"

CRITERIA: dict[str, Criterion] = {
    "1.1.1": Criterion("1.1.1", "Non-text Content", _BASE + "non-text-content.html"),
    "1.3.1": Criterion("1.3.1", "Info and Relationships", _BASE + "info-and-relationships.html"),
    "1.3.2": Criterion("1.3.2", "Meaningful Sequence", _BASE + "meaningful-sequence.html"),
    "2.4.3": Criterion("2.4.3", "Focus Order", _BASE + "focus-order.html"),
    "2.4.6": Criterion("2.4.6", "Headings and Labels", _BASE + "headings-and-labels.html"),
    "2.5.8": Criterion("2.5.8", "Target Size (Minimum)", _BASE + "target-size-minimum.html"),
    "3.3.2": Criterion("3.3.2", "Labels or Instructions", _BASE + "labels-or-instructions.html"),
    "4.1.2": Criterion("4.1.2", "Name, Role, Value", _BASE + "name-role-value.html"),
}


def criterion(cid: str) -> Criterion:
    return CRITERIA.get(cid, Criterion(cid, "Unknown", _BASE))
