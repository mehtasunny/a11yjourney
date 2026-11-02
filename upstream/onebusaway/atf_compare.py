"""Compare A11yJourney findings with Google's Accessibility Test Framework, screen by screen.

Matching is by issue family (labels, contrast, touch targets, and so on) on the same screen,
because the two tools describe elements differently. Usage: atf_compare.py AUDIT_DIR
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

ATF_FAMILY = {
    "SpeakableTextPresentCheck": "label", "EditableContentDescCheck": "label",
    "RedundantDescriptionCheck": "label", "DuplicateSpeakableTextCheck": "label",
    "LinkPurposeUnclearCheck": "label", "UnexposedTextCheck": "label",
    "ClassNameCheck": "role", "TextContrastCheck": "contrast", "ImageContrastCheck": "contrast",
    "TouchTargetSizeCheck": "target", "DuplicateClickableBoundsCheck": "target",
    "TraversalOrderCheck": "order", "TextSizeCheck": "text-size", "ClickableSpanCheck": "role",
}
WCAG_FAMILY = {
    "1.1.1": "label", "4.1.2": "label", "2.4.6": "label", "2.4.4": "label", "3.3.2": "label",
    "android-redundant-role": "label", "android-editable-description": "label",
    "1.4.3": "contrast", "1.4.11": "contrast", "2.5.5": "target", "2.5.8": "target",
    "android-touch-target": "target", "android-duplicate-clickable": "target",
    "2.4.3": "order", "1.4.4": "text-size", "2.1.1": "keyboard", "2.1.2": "keyboard",
}
SCREENS = {"home": "screens/home", "arrivals": "screens/arrivals", "settings": "settings/settings",
           "customer-service": "feedback/customer-service"}


def a11yjourney(build: Path, screen: str):
    rel = SCREENS[screen]
    report = build / rel.split("/")[0] / "report.json"
    if not report.exists():
        return None
    out = []
    for s in json.loads(report.read_text()):
        if Path(s["target"]).stem == Path(rel).name:
            out += [(WCAG_FAMILY.get(f["wcag"], f["wcag"]), f["wcag"], f["element"])
                    for f in s["findings"]]
            return out
    return None


def atf(build: Path, screen: str):
    p = build / "atf" / f"{screen}.jsonl"
    if not p.exists():
        return None
    out = []
    for line in p.read_text().splitlines():
        o = json.loads(line)
        if "check" in o:
            out.append((ATF_FAMILY.get(o["check"], o["check"]), o["check"],
                        o.get("desc") if o.get("desc") not in (None, "null") else o.get("text")))
    return out


def main(root: Path) -> None:
    print("# A11yJourney and Google's Accessibility Test Framework, side by side\n")
    print("Families compared on the same screen of the same build. A screen counts as agreeing on a")
    print("family when both tools report at least one issue in it.\n")
    totals = defaultdict(int)
    for build in ("baseline", "patched"):
        print(f"## {build}\n")
        print("| Screen | Family | A11yJourney | Google ATF | Agree |")
        print("|---|---|---|---|---|")
        for screen in SCREENS:
            a, g = a11yjourney(root / build, screen), atf(root / build, screen)
            if a is None or g is None:
                print(f"| {screen} | (not captured by {'A11yJourney' if a is None else 'ATF'}) | | | |")
                continue
            fams = sorted({x[0] for x in a} | {x[0] for x in g})
            if not fams:
                print(f"| {screen} | none | 0 | 0 | yes |")
                totals["both_clean"] += 1
            for fam in fams:
                na = [x for x in a if x[0] == fam]
                ng = [x for x in g if x[0] == fam]
                agree = "yes" if na and ng else "no"
                totals["agree" if na and ng else ("only_a11yjourney" if na else "only_atf")] += 1
                show = lambda xs: f"{len(xs)}: " + "; ".join(sorted({f'{x[1]} {x[2]}'[:50] for x in xs}))[:160] if xs else "0"
                print(f"| {screen} | {fam} | {show(na)} | {show(ng)} | {agree} |")
        print()
    print("## Totals (screen and family pairs)\n")
    for k in ("agree", "only_a11yjourney", "only_atf", "both_clean"):
        print(f"- {k.replace('_', ' ')}: {totals[k]}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
