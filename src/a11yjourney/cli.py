"""Command-line interface."""
from __future__ import annotations

import argparse
import sys

from .checks import run
from .model import load
from .reporters import FORMATTERS, summarize
from .wcag import Severity

_ORDER = {Severity.MODERATE: 0, Severity.SERIOUS: 1, Severity.CRITICAL: 2}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="a11yjourney",
        description="Journey-based, semantic accessibility auditing for native mobile apps.",
    )
    p.add_argument("dump", help="Path to a uiautomator accessibility-tree XML dump.")
    p.add_argument("-f", "--format", choices=list(FORMATTERS), default="text")
    p.add_argument("--min-severity", choices=[s.value for s in Severity], default="moderate")
    p.add_argument("--fail-on-findings", action="store_true",
                   help="Exit non-zero if any finding at or above --min-severity (CI gate).")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    findings = run(load(args.dump))
    threshold = _ORDER[Severity(args.min_severity)]
    findings = [f for f in findings if _ORDER[f.severity] >= threshold]
    sys.stdout.write(FORMATTERS[args.format](args.dump, findings) + "\n")
    if args.fail_on_findings and summarize(findings)["total"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
