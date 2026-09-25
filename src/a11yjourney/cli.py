"""Command-line interface.

    a11yjourney capture --name login          # from a connected Android device
    a11yjourney captures/login.xml            # audit a capture
"""
from __future__ import annotations

import argparse
import sys

from . import __version__, imaging
from .capture import CaptureError, adb_runner, capture, siblings
from .checks import audit
from .judge import ModelJudge, make_judge
from .model import load
from .reporters import FORMATTERS, in_scope
from .wcag import PROFILES, Severity

_ORDER = {Severity.MODERATE: 0, Severity.SERIOUS: 1, Severity.CRITICAL: 2}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="a11yjourney",
        description="Accessibility auditing for native Android apps: structural, contrast, "
                    "large-text, semantic, and journey checks mapped to WCAG.",
        epilog="To capture a screen from a connected device first, run "
               "`a11yjourney capture --help`.",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    p.add_argument("dump", help="A uiautomator accessibility-tree XML file.")
    p.add_argument("--screenshot", metavar="PNG",
                   help="Screenshot taken with the dump (enables contrast checks). "
                        "Default: NAME.png next to the dump, if present.")
    p.add_argument("--large-text", metavar="XML",
                   help="The same screen captured at 200%% font scale (enables the "
                        "resize-text check). Default: NAME.large.xml, if present.")
    p.add_argument("--tree-only", action="store_true",
                   help="Ignore screenshot and large-text files next to the dump.")
    p.add_argument("--density", type=float,
                   help="Screen density (dpi / 160) for dumps that do not record it.")
    p.add_argument("--standard", choices=list(PROFILES), default="wcag21-aa",
                   help="Conformance target. Default wcag21-aa, the level required by the "
                        "ADA Title II and HHS Section 504 rules.")
    p.add_argument("-f", "--format", choices=list(FORMATTERS), default="text")
    p.add_argument(
        "--judge", choices=["auto", "heuristic", "model"], default="heuristic",
        help="Semantic judge: 'heuristic' (offline default), 'model' (needs a provider key "
             "and --model), or 'auto' (model when both are configured).",
    )
    p.add_argument("--model", help="Model name for the model judge (or A11YJOURNEY_MODEL).")
    p.add_argument("--no-redact", action="store_true",
                   help="Send screen text to the model without redacting personal data.")
    p.add_argument("--min-severity", choices=[s.value for s in Severity], default="moderate")
    p.add_argument("--fail-on-findings", action="store_true",
                   help="Exit 1 if any conformance finding is at or above --min-severity "
                        "(advisory findings never fail the gate).")
    return p


def build_capture_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="a11yjourney capture",
        description="Capture the screen currently shown on a connected Android device: "
                    "accessibility tree, screenshot, and the tree again at 200% font scale.",
    )
    p.add_argument("--name", required=True, help="Base name for the files, e.g. login.")
    p.add_argument("--out", default="captures", help="Output folder (default: captures).")
    p.add_argument("--serial", help="Device serial, when more than one is connected.")
    p.add_argument("--adb", default="adb", help="Path to adb (default: adb on PATH).")
    p.add_argument("--no-large-text", action="store_true",
                   help="Skip the 200%% font-scale pass.")
    return p


def _capture_main(argv: list[str]) -> int:
    args = build_capture_parser().parse_args(argv)
    try:
        c = capture(adb_runner(args.serial, args.adb), args.out, args.name,
                    large_text=not args.no_large_text)
    except CaptureError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2
    for path in (c.tree, c.screenshot, c.large, c.manifest):
        if path:
            sys.stdout.write(f"wrote {path}\n")
    sys.stdout.write(f"\nNext: a11yjourney {c.tree}\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "capture":
        return _capture_main(argv[1:])

    args = build_parser().parse_args(argv)
    try:
        judge = make_judge(args.judge, args.model, redact=not args.no_redact)
    except RuntimeError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2

    shot_path, large_path = args.screenshot, args.large_text
    if not args.tree_only:
        auto_shot, auto_large = siblings(args.dump)
        shot_path = shot_path or auto_shot
        large_path = large_path or auto_large

    try:
        screen = load(args.dump, args.density)
        image = imaging.read(shot_path) if shot_path else None
        scaled = load(large_path, args.density or screen.density) if large_path else None
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2

    result = audit(screen, judge, image=image, scaled=scaled)
    profile = PROFILES[args.standard]
    threshold = _ORDER[Severity(args.min_severity)]
    findings = [f for f in result.findings if _ORDER[f.severity] >= threshold]
    notes = list(result.notes)
    notes.append("inputs: tree" + (f", screenshot {shot_path}" if shot_path else "")
                 + (f", large-text {large_path}" if large_path else ""))
    sys.stdout.write(FORMATTERS[args.format](args.dump, findings, profile, notes) + "\n")

    if isinstance(judge, ModelJudge) and judge.errors:
        sys.stderr.write(
            f"warning: the model judge failed on {judge.errors} of {judge.calls} calls "
            f"(last: {judge.last_error}); the heuristic decided those elements.\n")
    if args.fail_on_findings and any(in_scope(f, profile) for f in findings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
