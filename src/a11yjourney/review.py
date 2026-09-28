"""Measuring accuracy on real apps: review sheets and scores.

Automated accessibility checks are only as good as their false-positive and miss
rates, and those can only be measured against a person's judgment. The workflow:

1. ``a11yjourney report FOLDER --review-sheet review.csv`` writes one row per finding.
2. A reviewer checks each finding on the device (TalkBack, large text, a color picker)
   and fills in ``verdict``: ``confirmed``, ``false positive``, or ``unclear``.
3. The reviewer adds a row with verdict ``missed`` for every real problem found by hand
   that the tool did not report.
4. ``a11yjourney score review.csv`` reports precision (confirmed / judged findings) and
   recall (confirmed / (confirmed + missed)), overall and per check kind.
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from collections.abc import Sequence
from typing import Any

from .findings import Finding
from .reporters import in_scope
from .wcag import Profile, criterion

COLUMNS = ["app", "screen", "element", "wcag", "criterion", "in_scope", "kind", "severity",
           "needs_review", "message", "verdict", "reviewer_notes"]
VERDICTS = {"confirmed", "false positive", "unclear", "missed"}


def write_sheet(path: str, app: str, screens: Sequence[tuple[str, Sequence[Finding]]],
                profile: Profile) -> int:
    rows = 0
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        for screen, findings in screens:
            for f in findings:
                w.writerow({
                    "app": app, "screen": screen, "element": f.element, "wcag": f.wcag,
                    "criterion": criterion(f.wcag).name, "in_scope": in_scope(f, profile),
                    "kind": f.kind, "severity": f.severity.value, "needs_review": f.review,
                    "message": f.message, "verdict": "", "reviewer_notes": "",
                })
                rows += 1
    return rows


def _pct(n: int, d: int) -> float | None:
    return round(100.0 * n / d, 1) if d else None


def score(paths: Sequence[str]) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    by_kind: dict[str, Counter[str]] = defaultdict(Counter)
    apps: set[str] = set()
    for path in paths:
        with open(path, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                verdict = (row.get("verdict") or "").strip().lower()
                if not verdict:
                    counts["unreviewed"] += 1
                    continue
                if verdict not in VERDICTS:
                    raise ValueError(f"{path}: unknown verdict {verdict!r}")
                counts[verdict] += 1
                by_kind[row.get("kind") or "?"][verdict] += 1
                apps.add(row.get("app") or "?")

    def metrics(c: Counter[str]) -> dict[str, Any]:
        judged = c["confirmed"] + c["false positive"]
        return {
            "confirmed": c["confirmed"], "false_positive": c["false positive"],
            "unclear": c["unclear"], "missed": c["missed"],
            "precision_pct": _pct(c["confirmed"], judged),
            "recall_pct": _pct(c["confirmed"], c["confirmed"] + c["missed"]),
        }

    return {"apps": sorted(apps), "unreviewed": counts["unreviewed"],
            "overall": metrics(counts),
            "by_kind": {k: metrics(v) for k, v in sorted(by_kind.items())}}


def format_score(result: dict[str, Any]) -> str:
    def line(name: str, m: dict[str, Any]) -> str:
        p = "n/a" if m["precision_pct"] is None else f"{m['precision_pct']}%"
        r = "n/a" if m["recall_pct"] is None else f"{m['recall_pct']}%"
        return (f"{name:<12} precision {p:>7}  recall {r:>7}  (confirmed {m['confirmed']}, "
                f"false positive {m['false_positive']}, unclear {m['unclear']}, "
                f"missed {m['missed']})")

    out = [f"apps: {', '.join(result['apps']) or 'none'}",
           line("overall", result["overall"])]
    out += [line(k, m) for k, m in result["by_kind"].items()]
    if result["unreviewed"]:
        out.append(f"{result['unreviewed']} finding(s) not reviewed yet; they are not counted.")
    return "\n".join(out)
