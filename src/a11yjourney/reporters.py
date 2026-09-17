"""Output formats: human text, JSON, and SARIF 2.1.0 for GitHub code scanning."""
from __future__ import annotations

import json

from .checks import Finding
from .wcag import criterion


def summarize(findings: list[Finding]) -> dict[str, int]:
    structural = sum(1 for f in findings if f.kind == "STRUCTURAL")
    return {
        "total": len(findings),
        "structural": structural,
        "beyond_static": len(findings) - structural,
    }


def to_text(path: str, findings: list[Finding]) -> str:
    s = summarize(findings)
    lines = [
        f"A11yJourney report: {path}",
        f"{s['total']} findings  |  {s['structural']} structural  |  "
        f"{s['beyond_static']} semantic/journey (undetectable by static scanners)",
        "",
    ]
    for f in findings:
        c = criterion(f.wcag)
        lines.append(f"  [{f.kind}] {f.severity.value.upper()}  WCAG {c.id} {c.name}")
        lines.append(f"        {f.element}: {f.message}")
    return "\n".join(lines)


def to_json(path: str, findings: list[Finding]) -> str:
    return json.dumps(
        {
            "target": path,
            "summary": summarize(findings),
            "findings": [
                {
                    "kind": f.kind,
                    "severity": f.severity.value,
                    "wcag": f.wcag,
                    "criterion": criterion(f.wcag).name,
                    "element": f.element,
                    "message": f.message,
                }
                for f in findings
            ],
        },
        indent=2,
    )


def to_sarif(path: str, findings: list[Finding]) -> str:
    rule_ids = sorted({f.wcag for f in findings})
    rules = [
        {
            "id": f"WCAG-{rid}",
            "name": criterion(rid).name.replace(" ", ""),
            "shortDescription": {"text": f"WCAG {rid} {criterion(rid).name}"},
            "helpUri": criterion(rid).url,
        }
        for rid in rule_ids
    ]
    results = [
        {
            "ruleId": f"WCAG-{f.wcag}",
            "level": f.severity.sarif_level,
            "message": {"text": f"[{f.kind}] {f.element}: {f.message}"},
            "locations": [
                {"physicalLocation": {"artifactLocation": {"uri": path}}}
            ],
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
                "results": results,
            }
        ],
    }
    return json.dumps(doc, indent=2)


FORMATTERS = {"text": to_text, "json": to_json, "sarif": to_sarif}
