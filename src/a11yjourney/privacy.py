"""Redaction of personal data before any text leaves the machine.

Health, transit, and government apps show personal information on screen:
names, dates of birth, member IDs, phone numbers, addresses. When the model
judge is enabled, element labels and nearby screen text are sent to a model
provider. Redaction is on by default and replaces the common patterns below
with placeholders before a prompt is built.

This is a safety net, not a guarantee. Pattern matching cannot recognize every
name or free-text detail, so prefer test accounts and synthetic data when
auditing screens that show real records.
"""
from __future__ import annotations

import re

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+"), "[email]"),
    (re.compile(r"https?://\S+"), "[url]"),
    (re.compile(r"\b\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+"
                r"(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Dr|Drive|Ln|Lane|Way|Ct)\b\.?"),
     "[address]"),
    (re.compile(r"\b\d{1,4}[/.-]\d{1,2}[/.-]\d{2,4}\b"), "[date]"),
    # phone numbers, IDs, card and account numbers: any run of 4+ digits,
    # allowing the separators people type between groups
    (re.compile(r"\+?\(?\d(?:[\d\s().-]*\d){3,}"), "[number]"),
]


def redact(text: str) -> str:
    """Replace emails, URLs, dates, long numbers, and street addresses."""
    for pattern, placeholder in _PATTERNS:
        text = pattern.sub(placeholder, text)
    return text
