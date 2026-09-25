"""Coverage benchmark.

Measures how much of a screen's *genuine* accessibility problems each mode
recovers: a static-only scanner (presence/absence checks) versus the full
A11yJourney engine (structural + semantic + journey). Ground truth is the
labeled corpus, declared independently of the engine.

Metrics per the usual detection framing:
  recall    = true issues detected / all true issues        (coverage)
  precision = true issues detected / all issues reported
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass

from .checks import run
from .judge import Judge
from .model import load

Pair = tuple[str, str]  # (element, criterion family)

# Criteria that describe the same defect at different thresholds. Ground truth
# says "this target is too small"; the engine reports it under whichever
# threshold it fails (2.5.8, 2.5.5, or the Android 48dp guidance).
_FAMILIES = {"2.5.8": "target-size", "2.5.5": "target-size",
             "android-touch-target": "target-size"}


def _family(wcag: str) -> str:
    return _FAMILIES.get(wcag, wcag)


@dataclass(frozen=True)
class CaseResult:
    name: str
    gt_total: int
    gt_static: int
    gt_judgment: int
    static_hits: int
    full_hits: int
    full_reported: int


def _gt_pairs(expected_path: pathlib.Path) -> tuple[set[Pair], set[Pair]]:
    data = json.loads(expected_path.read_text())
    static: set[Pair] = set()
    judgment: set[Pair] = set()
    for g in data["ground_truth"]:
        pair = (g["element"], _family(g["wcag"]))
        (static if g["class"] == "static" else judgment).add(pair)
    return static, judgment


def evaluate_case(
    xml: pathlib.Path, expected: pathlib.Path, judge: Judge | None = None
) -> CaseResult:
    gt_static, gt_judgment = _gt_pairs(expected)
    gt = gt_static | gt_judgment
    findings = run(load(str(xml)), judge)
    detected_static = {(f.element, _family(f.wcag)) for f in findings
                       if f.kind == "STRUCTURAL"}
    detected_full = {(f.element, _family(f.wcag)) for f in findings}
    return CaseResult(
        name=xml.stem,
        gt_total=len(gt),
        gt_static=len(gt_static),
        gt_judgment=len(gt_judgment),
        static_hits=len(detected_static & gt),
        full_hits=len(detected_full & gt),
        full_reported=len(detected_full),
    )


def evaluate_corpus(corpus_dir: str, judge: Judge | None = None) -> list[CaseResult]:
    d = pathlib.Path(corpus_dir)
    results = []
    for xml in sorted(d.glob("*.xml")):
        expected = d / f"{xml.stem}.expected.json"
        if expected.exists():
            results.append(evaluate_case(xml, expected, judge))
    return results


def _pct(n: int, d: int) -> float:
    return round(100.0 * n / d, 1) if d else 0.0


def aggregate(results: list[CaseResult]) -> dict[str, float]:
    gt = sum(r.gt_total for r in results)
    return {
        "cases": len(results),
        "ground_truth_issues": gt,
        "static_recall_pct": _pct(sum(r.static_hits for r in results), gt),
        "full_recall_pct": _pct(sum(r.full_hits for r in results), gt),
        "full_precision_pct": _pct(sum(r.full_hits for r in results),
                                   sum(r.full_reported for r in results)),
    }


def format_markdown(results: list[CaseResult]) -> str:
    lines = ["| Screen | GT issues | static-only recall | full-engine recall |",
             "|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r.name} | {r.gt_total} | "
                     f"{_pct(r.static_hits, r.gt_total)}% | {_pct(r.full_hits, r.gt_total)}% |")
    agg = aggregate(results)
    lines.append(f"| **all** | **{agg['ground_truth_issues']}** | "
                 f"**{agg['static_recall_pct']}%** | **{agg['full_recall_pct']}%** |")
    return "\n".join(lines)
