"""The Finding record shared by every check."""
from __future__ import annotations

from dataclasses import dataclass

from .wcag import Severity

# Kinds of check that produce findings.
STRUCTURAL = "STRUCTURAL"  # presence/absence in the tree; what most scanners do
VISUAL = "VISUAL"  # measured from the screenshot (contrast)
RESIZE = "RESIZE"  # compares default and enlarged-text captures
SEMANTIC = "SEMANTIC"  # needs judgment about meaning or order
JOURNEY = "JOURNEY"  # can the task be completed at all

JUDGMENT_KINDS = frozenset({SEMANTIC, JOURNEY})


@dataclass(frozen=True)
class Finding:
    kind: str
    wcag: str
    severity: Severity
    element: str
    message: str
    review: bool = False  # True when the result is an estimate a person should confirm
