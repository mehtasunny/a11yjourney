"""Output formats: human text, JSON, and SARIF 2.1.0 for GitHub code scanning.

Every report is judged against a conformance profile (WCAG 2.1 AA by default,
the level U.S. rules require). Findings against criteria outside the profile
(WCAG 2.2-only, Level AAA, or platform guidance) are still reported, but as
advisory, so a report never overstates what the law requires.
"""
from __future__ import annotations

import json
from collections.abc import Sequence

from .findings import JUDGMENT_KINDS, STRUCTURAL, Finding
from .wcag import DEFAULT_PROFILE, Profile, criterion


def in_scope(f: Finding, profile: Profile = DEFAULT_PROFILE) -> bool:
    return profile.covers(criterion(f.wcag))


def summarize(findings: Sequence[Finding], profile: Profile = DEFAULT_PROFILE) -> dict[str, int]:
    scoped = sum(1 for f in findings if in_scope(f, profile))
    return {
        "total": len(findings),
        "conformance": scoped,
        "advisory": len(findings) - scoped,
        "structural": sum(1 for f in findings if f.kind == STRUCTURAL),
        "beyond_static": sum(1 for f in findings if f.kind in JUDGMENT_KINDS),
        "needs_review": sum(1 for f in findings if f.review),
    }


def _line(f: Finding) -> list[str]:
    c = criterion(f.wcag)
    flag = "  (estimate, confirm on device)" if f.review else ""
    return [f"  [{f.kind}] {f.severity.value.upper()}  {c.label}{flag}",
            f"        {f.element}: {f.message}"]


def to_text(path: str, findings: Sequence[Finding], profile: Profile = DEFAULT_PROFILE,
            notes: Sequence[str] = ()) -> str:
    s = summarize(findings, profile)
    lines = [
        f"A11yJourney report: {path}",
        f"Judged against {profile.title}",
        f"{s['conformance']} conformance findings  |  {s['advisory']} advisory  |  "
        f"{s['beyond_static']} need semantic judgment  |  {s['needs_review']} to confirm by hand",
        "",
    ]
    scoped = [f for f in findings if in_scope(f, profile)]
    advisory = [f for f in findings if not in_scope(f, profile)]
    if scoped:
        lines.append(f"Conformance findings ({profile.title}):")
        for f in scoped:
            lines += _line(f)
        lines.append("")
    if advisory:
        lines.append(f"Advisory (beyond {profile.title}, still worth fixing):")
        for f in advisory:
            lines += _line(f)
        lines.append("")
    if notes:
        lines.append("Notes:")
        lines += [f"  - {n}" for n in notes]
        lines.append("")
    lines.append("Automated checks find likely problems; they cannot certify conformance.")
    return "\n".join(lines)


def to_json(path: str, findings: Sequence[Finding], profile: Profile = DEFAULT_PROFILE,
            notes: Sequence[str] = ()) -> str:
    return json.dumps(
        {
            "target": path,
            "profile": {"key": profile.key, "wcag": profile.version, "level": profile.level},
            "summary": summarize(findings, profile),
            "findings": [
                {
                    "kind": f.kind,
                    "severity": f.severity.value,
                    "wcag": f.wcag,
                    "criterion": criterion(f.wcag).name,
                    "level": criterion(f.wcag).level,
                    "since": criterion(f.wcag).since or None,
                    "in_scope": in_scope(f, profile),
                    "needs_review": f.review,
                    "element": f.element,
                    "message": f.message,
                }
                for f in findings
            ],
            "notes": list(notes),
        },
        indent=2,
    )


def _rule_id(cid: str) -> str:
    return cid if cid.startswith("android-") else f"WCAG-{cid}"


def to_sarif(path: str, findings: Sequence[Finding], profile: Profile = DEFAULT_PROFILE,
             notes: Sequence[str] = ()) -> str:
    rules = [
        {
            "id": _rule_id(rid),
            "name": "".join(ch for ch in criterion(rid).name.title() if ch.isalnum()),
            "shortDescription": {"text": criterion(rid).label},
            "helpUri": criterion(rid).url,
        }
        for rid in sorted({f.wcag for f in findings})
    ]
    results = [
        {
            "ruleId": _rule_id(f.wcag),
            "level": f.severity.sarif_level if in_scope(f, profile) else "note",
            "message": {"text": f"[{f.kind}] {f.element}: {f.message}"},
            "locations": [{"physicalLocation": {"artifactLocation": {"uri": path}}}],
            "properties": {"inScope": in_scope(f, profile), "needsReview": f.review},
        }
        for f in findings
    ]
    doc = {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [
            {
                "tool": {"driver": {"name": "A11yJourney", "informationUri":
                         "https://github.com/mehtasunny/a11yjourney", "rules": rules}},
                "properties": {"profile": profile.key, "notes": list(notes)},
                "results": results,
            }
        ],
    }
    return json.dumps(doc, indent=2)


FORMATTERS = {"text": to_text, "json": to_json, "sarif": to_sarif}
