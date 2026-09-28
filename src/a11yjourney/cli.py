"""Command-line interface.

    a11yjourney capture --name login [--keyboard]   # one screen from a connected device
    a11yjourney journey steps.txt --out run1        # replay a scripted task
    a11yjourney explore --out run2                  # open each control once, carefully
    a11yjourney captures/login.xml                  # audit one capture
    a11yjourney report run1 --format sarif          # audit every capture in a folder
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from collections.abc import Callable

from . import __version__, imaging
from .capture import CaptureError, adb_runner, capture, focus_sibling, siblings
from .checks import audit
from .findings import Finding
from .journey import JourneyError, Session, explore, parse_steps, run_journey
from .judge import Judge, ModelJudge, make_judge
from .model import load
from .reporters import FORMATTERS, in_scope, summarize, to_json, to_sarif, to_text
from .review import format_score, score, write_sheet
from .wcag import PROFILES, Severity

_ORDER = {Severity.MODERATE: 0, Severity.SERIOUS: 1, Severity.CRITICAL: 2}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="a11yjourney",
        description="Accessibility auditing for native Android apps: structural, contrast, "
                    "large-text, semantic, and journey checks mapped to WCAG.",
        epilog="Other commands: capture (one screen from a device), journey (replay a "
               "scripted task), explore (open each control once), report (audit a folder), "
               "score (precision and recall from reviewed sheets). "
               "Run `a11yjourney COMMAND --help` for each.",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    p.add_argument("dump", help="A uiautomator accessibility-tree XML file.")
    p.add_argument("--screenshot", metavar="PNG",
                   help="Screenshot taken with the dump (enables contrast checks). "
                        "Default: NAME.png next to the dump, if present.")
    p.add_argument("--large-text", metavar="XML",
                   help="The same screen captured at 200%% font scale (enables the "
                        "resize-text check). Default: NAME.large.xml, if present.")
    p.add_argument("--focus-trace", metavar="JSON",
                   help="Keyboard focus sequence recorded on the device (enables measured "
                        "focus-order and keyboard checks). Default: NAME.focus.json, if present.")
    p.add_argument("--tree-only", action="store_true",
                   help="Ignore screenshot, large-text, and focus files next to the dump.")
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
    p.add_argument("--keyboard", action="store_true",
                   help="Also press Tab through the screen and record the real keyboard "
                        "focus order (adds 20 to 60 seconds).")
    return p


def _capture_main(argv: list[str]) -> int:
    args = build_capture_parser().parse_args(argv)
    try:
        c = capture(adb_runner(args.serial, args.adb), args.out, args.name,
                    large_text=not args.no_large_text, keyboard=args.keyboard)
    except CaptureError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2
    for path in (c.tree, c.screenshot, c.large, c.focus, c.manifest):
        if path:
            sys.stdout.write(f"wrote {path}\n")
    sys.stdout.write(f"\nNext: a11yjourney {c.tree}\n")
    return 0


def _audit_file(path: str, args: argparse.Namespace, judge: Judge,
                ) -> tuple[list[Finding], list[str]]:
    """Audit one captured tree, picking up its screenshot, large-text, and focus files."""
    shot_path = getattr(args, "screenshot", None)
    large_path = getattr(args, "large_text", None)
    focus_path = getattr(args, "focus_trace", None)
    if not getattr(args, "tree_only", False):
        auto_shot, auto_large = siblings(path)
        shot_path = shot_path or auto_shot
        large_path = large_path or auto_large
        focus_path = focus_path or focus_sibling(path)
    screen = load(path, args.density)
    image = imaging.read(shot_path) if shot_path else None
    scaled = load(large_path, args.density or screen.density) if large_path else None
    trace = None
    if focus_path:
        with open(focus_path, encoding="utf-8") as fh:
            trace = json.load(fh)
    result = audit(screen, judge, image=image, scaled=scaled, focus_trace=trace)
    threshold = _ORDER[Severity(args.min_severity)]
    findings = [f for f in result.findings if _ORDER[f.severity] >= threshold]
    notes = list(result.notes)
    notes.append("inputs: tree" + (f", screenshot {shot_path}" if shot_path else "")
                 + (f", large-text {large_path}" if large_path else "")
                 + (f", keyboard focus {focus_path}" if focus_path else ""))
    return findings, notes


def _warn_model(judge: Judge) -> None:
    if isinstance(judge, ModelJudge) and judge.errors:
        sys.stderr.write(
            f"warning: the model judge failed on {judge.errors} of {judge.calls} calls "
            f"(last: {judge.last_error}); the heuristic decided those elements.\n")


def _add_audit_options(p: argparse.ArgumentParser) -> None:
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


def _device_parser(prog: str, description: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog=prog, description=description)
    p.add_argument("--out", default="captures", help="Output folder (default: captures).")
    p.add_argument("--serial", help="Device serial, when more than one is connected.")
    p.add_argument("--adb", default="adb", help="Path to adb (default: adb on PATH).")
    return p


def _journey_main(argv: list[str]) -> int:
    p = _device_parser("a11yjourney journey",
                       "Replay a journey script on the connected device and capture each "
                       "screen it names. See the journey module docs for the step syntax.")
    p.add_argument("script", help="Text file with one step per line.")
    args = p.parse_args(argv)
    try:
        with open(args.script, encoding="utf-8") as fh:
            steps = parse_steps(fh.read())
        session = Session(adb_runner(args.serial, args.adb), pathlib.Path(args.out))
        captured = run_journey(session, steps)
    except (OSError, JourneyError, CaptureError) as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2
    sys.stdout.write("".join(f"captured {c}\n" for c in captured))
    sys.stdout.write(f"\nNext: a11yjourney report {args.out}\n")
    return 0


def _explore_main(argv: list[str]) -> int:
    p = _device_parser("a11yjourney explore",
                       "Open each control on the current screen once, capture any new screen "
                       "it leads to, and come back. Taps real controls: use a test device "
                       "and a test account.")
    p.add_argument("--max-screens", type=int, default=8)
    p.add_argument("--keyboard", action="store_true",
                   help="Also measure keyboard focus on each captured screen.")
    p.add_argument("--allow-risky", action="store_true",
                   help="Also tap controls labeled like delete, pay, send, sign out.")
    args = p.parse_args(argv)
    try:
        session = Session(adb_runner(args.serial, args.adb), pathlib.Path(args.out))
        result = explore(session, args.max_screens, args.allow_risky, args.keyboard)
    except (JourneyError, CaptureError) as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2
    for v in result["visits"]:
        sys.stdout.write(f"{v['control']}: {v['result']}\n")
    sys.stdout.write(f"\n{len(result['captures'])} screens captured. "
                     f"Next: a11yjourney report {args.out}\n")
    return 0


def _report_main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        prog="a11yjourney report",
        description="Audit every capture in a folder (from capture, journey, or explore).")
    p.add_argument("folder")
    _add_audit_options(p)
    p.add_argument("--review-sheet", metavar="CSV",
                   help="Also write every finding to a CSV with an empty verdict column, "
                        "for confirming each one by hand (see `a11yjourney score`).")
    args = p.parse_args(argv)
    trees = sorted(str(t) for t in pathlib.Path(args.folder).glob("*.xml")
                   if not t.name.endswith(".large.xml"))
    if not trees:
        sys.stderr.write(f"error: no captures in {args.folder}\n")
        return 2
    try:
        judge = make_judge(args.judge, args.model, redact=not args.no_redact)
        results = [(t, *_audit_file(t, args, judge)) for t in trees]
    except (OSError, ValueError, RuntimeError) as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2
    profile = PROFILES[args.standard]
    if args.review_sheet:
        write_sheet(args.review_sheet, pathlib.Path(args.folder).name,
                    [(pathlib.Path(t).stem, fs) for t, fs, _ in results], profile)
    if args.format == "text":
        rows = [f"{'screen':<32} {'conformance':>11} {'advisory':>9} {'to confirm':>11}"]
        for t, fs, _ in results:
            sm = summarize(fs, profile)
            rows.append(f"{pathlib.Path(t).stem:<32} {sm['conformance']:>11} "
                        f"{sm['advisory']:>9} {sm['needs_review']:>11}")
        sys.stdout.write("\n".join(rows) + "\n\n")
        for t, fs, notes in results:
            sys.stdout.write(to_text(t, fs, profile, notes) + "\n\n")
    elif args.format == "json":
        sys.stdout.write(json.dumps([json.loads(to_json(t, fs, profile, n))
                                     for t, fs, n in results], indent=2) + "\n")
    else:
        docs = [json.loads(to_sarif(t, fs, profile, n)) for t, fs, n in results]
        merged = docs[0]
        run = merged["runs"][0]
        rules = {r["id"]: r for d in docs for r in d["runs"][0]["tool"]["driver"]["rules"]}
        run["tool"]["driver"]["rules"] = sorted(rules.values(), key=lambda r: r["id"])
        run["results"] = [r for d in docs for r in d["runs"][0]["results"]]
        run["properties"]["notes"] = [n for d in docs for n in d["runs"][0]["properties"]["notes"]]
        sys.stdout.write(json.dumps(merged, indent=2) + "\n")
    _warn_model(judge)
    if args.fail_on_findings and any(in_scope(f, profile) for _, fs, _ in results for f in fs):
        return 1
    return 0


def _score_main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        prog="a11yjourney score",
        description="Precision and recall from review sheets whose verdict column has been "
                    "filled in by hand: confirmed, false positive, unclear, or missed (a real "
                    "problem the tool did not report, added as its own row).")
    p.add_argument("sheets", nargs="+")
    p.add_argument("-f", "--format", choices=["text", "json"], default="text")
    args = p.parse_args(argv)
    try:
        result = score(args.sheets)
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2
    if args.format == "json":
        sys.stdout.write(json.dumps(result, indent=2) + "\n")
    else:
        sys.stdout.write(format_score(result) + "\n")
    return 0


_SUBCOMMANDS: dict[str, Callable[[list[str]], int]] = {
    "score": _score_main,
    "capture": _capture_main,
    "journey": _journey_main,
    "explore": _explore_main,
    "report": _report_main,
}


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] in _SUBCOMMANDS:
        return _SUBCOMMANDS[argv[0]](argv[1:])

    args = build_parser().parse_args(argv)
    try:
        judge = make_judge(args.judge, args.model, redact=not args.no_redact)
    except RuntimeError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2
    try:
        findings, notes = _audit_file(args.dump, args, judge)
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2
    profile = PROFILES[args.standard]
    sys.stdout.write(FORMATTERS[args.format](args.dump, findings, profile, notes) + "\n")
    _warn_model(judge)
    if args.fail_on_findings and any(in_scope(f, profile) for f in findings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
