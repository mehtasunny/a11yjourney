# Architecture

A11yJourney is a small, layered pipeline with one deliberately swappable seam
(the judge) and no required dependencies.

```
connected phone (adb)
   capture.py        uiautomator dump + screencap + second dump at font scale 2.0
        |
   NAME.xml   NAME.png   NAME.large.xml   NAME.json (manifest)
        |
   model.py          parse into typed Node / Screen; work out what TalkBack announces
        |
   checks.audit(screen, judge, image=..., scaled=...)
        |   +-- structural   names, field labels, target size (with 2.5.8 spacing rule)
        |   +-- contrast.py  text 1.4.3 and icon 1.4.11, estimated from screenshot pixels
        |   +-- resize.py    1.4.4, comparing normal and 200% font-scale trees
        |   +-- semantic     meaningful labels, focus order          ----+
        |   +-- journey      can the primary action be identified    ----+---> Judge
        |
   reporters.py      text | JSON | SARIF, each judged against a conformance Profile
```

## Modules

| Module | Responsibility |
|---|---|
| `capture.py` | Runs adb, stamps screen density into the dump, restores the font scale afterwards. adb is injected as a function so it can be tested without a device. |
| `model.py` | Parses `uiautomator dump` XML. `Node.announced` approximates what TalkBack says: own name, a field's hint, or descendant text for unlabeled containers. |
| `imaging.py` | Standard-library PNG decoder and encoder, and the WCAG luminance and contrast formulas. |
| `contrast.py` | Estimates foreground and background colors per element. Skips disabled controls and elements with no uniform background rather than guessing. |
| `resize.py` | Matches text elements between the two captures and reports text that vanishes, overlaps, runs off screen, or does not grow. Skips the comparison if the larger font scale evidently was not applied. |
| `checks.py` | Orchestrates the checks and returns an `Audit` (findings plus notes on anything skipped). |
| `judge.py` | `HeuristicJudge` (offline) and `ModelJudge` (any `complete(prompt) -> str`), with adapters for Anthropic and OpenAI-compatible APIs. |
| `privacy.py` | Redacts personal data from anything placed in a model prompt. |
| `wcag.py` | Registry of criteria with level and the WCAG version that introduced them, plus conformance `Profile`s. |
| `reporters.py` | Output formats. Findings outside the profile are labeled advisory (SARIF level `note`). |
| `benchmark.py` | Recall and precision against a labeled corpus. |

## Design principles

- **Zero required dependencies.** Parsing, image decoding, checks, provider
  calls, and reporting use only the standard library, so the tool installs
  anywhere and is easy to adopt in CI.
- **Never overstate.** Every finding cites a criterion and its level, reports
  separate what the chosen standard requires from what is advisory, and
  estimates are marked for a person to confirm.
- **Skip rather than guess.** When an input is missing or unusable (no
  density, a screenshot that does not match the tree, a font scale that did
  not apply), the check is skipped and the report says why.
- **Private by default.** The default judge is offline. The model judge
  redacts personal data and never sees text typed into fields.

## Extending

- **New check:** add it in `checks.py` or its own module, map it to a
  criterion in `wcag.py`, and cover it with a test.
- **Real model:** `ModelJudge(complete)` accepts any callable; pass it to
  `audit()` or use `--judge model --model NAME`.
- **Another platform:** write a loader that produces a `Screen`; the checks and
  reporters do not depend on Android beyond the tree's vocabulary.
