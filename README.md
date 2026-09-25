# A11yJourney

**Accessibility checks for native Android apps, aimed at the health, public
transit, and government apps that new U.S. accessibility rules now cover.**

[![ci](https://github.com/mehtasunny/a11yjourney/actions/workflows/ci.yml/badge.svg)](https://github.com/mehtasunny/a11yjourney/actions)
[![python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![license: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A11yJourney captures a screen from a connected Android phone and reports the
barriers people actually run into: controls a screen reader cannot name, text
too faint to read, text that breaks at the large font sizes many low-vision
users rely on, touch targets too small for people with tremors, and labels
that exist but say nothing useful. Every finding cites a WCAG success
criterion, and every report says plainly whether that criterion is required
by the standard you are held to.

It is a command-line tool with no required dependencies, and it writes text,
JSON, or SARIF, so results can show up on pull requests through GitHub code
scanning.

> **Status: v0.2.1, early.** The checks below work and are covered by tests
> and a small synthetic benchmark. The first run on a real Jetpack Compose app
> exposed false positives, now fixed and kept fixed by tests on those
> captures. Field validation on open-source apps is in progress (see
> [docs/field-validation.md](docs/field-validation.md)). Until that is
> published, treat findings as leads to confirm, not verdicts.

## What it checks

| Check | WCAG | What it needs | Who it helps |
|---|---|---|---|
| Controls with no accessible name, fields with no label | 4.1.2, 3.3.2 | tree | screen-reader users |
| Labels that are present but meaningless ("button1", "ic_img_2.png") | 2.4.6, 1.1.1 | tree + judge | screen-reader users |
| Focus order that does not match the visual order | 2.4.3 | tree | screen-reader and switch users |
| Text and icon contrast | 1.4.3, 1.4.11 | tree + screenshot | low vision, color blindness, glare |
| Text that disappears, overlaps, or clips at 200% font size | 1.4.4 | tree at normal and 200% text | low vision |
| Touch target size | 2.5.8, 2.5.5, Android 48dp | tree | tremor, limited dexterity |

## Quick start

```bash
git clone https://github.com/mehtasunny/a11yjourney && cd a11yjourney
pip install -e .

# try it on the included synthetic transit screen
a11yjourney examples/transit/trip.xml
```

With a phone connected over USB (developer options and USB debugging on,
`adb` from Android platform-tools on your PATH), open the screen you want to
check and run:

```bash
a11yjourney capture --name trip        # tree, screenshot, and 200% text pass
a11yjourney captures/trip.xml          # picks up trip.png and trip.large.xml
```

`capture` records the screen density, which the size checks need, and puts
your font size back when it finishes, even if something fails.

Part of the report for the example screen:

```
Judged against WCAG 2.1 Level AA
6 conformance findings  |  4 advisory  |  0 need semantic judgment  |  5 to confirm by hand

Conformance findings (WCAG 2.1 Level AA):
  [STRUCTURAL] SERIOUS  WCAG 3.3.2 Labels or Instructions, Level A
        to: Input field has no programmatic label.
  [VISUAL] SERIOUS  WCAG 1.4.3 Contrast (Minimum), Level AA  (estimate, confirm on device)
        leave: Text contrast is about 2.4:1 (#A8A8A8 on #FFFFFF); WCAG AA needs 4.5:1, ...
  [RESIZE] SERIOUS  WCAG 1.4.4 Resize Text, Level AA  (estimate, confirm on device)
        alert: Text is no longer on screen at 200% font size and is not in a scrolling ...
```

## Why it exists

Two federal rules adopted in 2024 require WCAG 2.1 Level AA for the web
content **and mobile apps** of the organizations they cover, with deadlines
that are now close:

| Rule | Who it covers | Compliance dates |
|---|---|---|
| ADA Title II ([DOJ, as extended April 2026](https://www.federalregister.gov/documents/2026/04/20/2026-07663/extension-of-compliance-dates-for-nondiscrimination-on-the-basis-of-disability-accessibility-of-web)) | State and local governments, including public transit agencies | April 26, 2027 (population 50,000+); April 26, 2028 (smaller entities and special districts) |
| Section 504 ([HHS, as extended May 2026](https://www.federalregister.gov/documents/2026/05/11/2026-09266/extension-of-compliance-dates-for-nondiscrimination-on-the-basis-of-disability-accessibility-of-web)) | Recipients of HHS funding, such as hospitals, clinics, and state health and human services agencies | May 11, 2027 (15+ employees); May 10, 2028 (fewer than 15) |

Section 508 already applies to federal agencies. More than 70 million adults
in the U.S. report a disability, and the apps these rules cover are the ones
people use to refill a prescription, catch a bus, or renew benefits.

Most of the teams building those apps are small and have no accessibility
specialist. Presence-only scanners help, but they cannot tell whether a label
means anything, whether text survives large font sizes, or whether a task can
be finished with a screen reader. A11yJourney is meant to make those checks
cheap enough to run on every build.

## Conformance profile: what is required versus advisory

Reports are judged against **WCAG 2.1 Level AA** by default, the level these
rules require. Findings against criteria outside the profile are still shown,
under "Advisory", and never fail the CI gate:

* **2.5.8 Target Size (Minimum)** is new in WCAG 2.2. Use `--standard wcag22-aa`
  to count it.
* **2.5.5 Target Size** is Level AAA.
* **Android's 48dp touch target** is platform guidance, not a WCAG criterion.

Sizes are measured in density-independent pixels (dp), which the W3C's
guidance on applying WCAG to non-web software (WCAG2ICT) uses as the
stand-in for CSS pixels.

## What automated checks cannot tell you

No tool can certify that an app conforms to WCAG. A11yJourney finds likely
problems on the screens you capture. It does not explore the app on its own,
and it cannot judge everything that needs a person, for example whether the
captions on a video are accurate. Findings marked **"estimate, confirm on
device"** come from pixels or from comparing captures and should be checked
with TalkBack or a person before they are reported as defects.

## Privacy

Screens in health, transit, and government apps often show personal data.

* Captures stay on your machine. Use test accounts where you can, and never
  commit captures of real records.
* The default judge is an offline heuristic. Nothing leaves the machine
  unless you turn on the model judge.
* When the model judge is on, emails, phone and ID numbers, dates, URLs, and
  street addresses are replaced with placeholders before any text is sent
  (`--no-redact` turns this off). Pattern matching cannot catch every name, so
  prefer synthetic data.
* Text typed into fields is never sent to the model.

## Semantic judge: heuristic or a real model

Whether a label is *meaningful* is a judgment call. The default
`HeuristicJudge` catches the obvious cases offline. For better judgment, use
any model you have access to. No model name is built in, because provider
model names change; pass the one you want:

```bash
export ANTHROPIC_API_KEY=...          # or OPENAI_API_KEY (+ OPENAI_BASE_URL for any
                                      #   OpenAI-compatible server, including local ones)
a11yjourney captures/trip.xml --judge model --model <model-name>
```

If calls fail (bad key, retired model, rate limit), the heuristic decides
those elements and the tool prints a warning with the count and the last
error, so a failed model never goes unnoticed.

## Use in CI

```yaml
- run: a11yjourney captures/trip.xml --format sarif > a11y.sarif
- uses: github/codeql-action/upload-sarif@v3
  with: { sarif_file: a11y.sarif }
- run: a11yjourney captures/trip.xml --min-severity serious --fail-on-findings
```

Advisory findings are uploaded with SARIF level `note` and do not fail the
gate.

## Coverage benchmark

`benchmark/` holds a small labeled corpus whose ground truth is declared
independently of the engine, and a runner that compares a presence-only mode
with the full engine:

```bash
python benchmark/run.py
```

On the current synthetic seed corpus (4 screens, 27 labeled issues, offline
heuristic judge), presence-only checks recover about 59% of the labeled issues
and the full engine about 85%. These numbers come from synthetic screens and
say nothing yet about real apps; see [docs/benchmark.md](docs/benchmark.md).

## How it works

| Layer | What it does |
|---|---|
| **Capture** | `adb`: `uiautomator dump`, `screencap`, and a second dump at font scale 2.0 |
| **Model** | Parses the tree into typed nodes; works out what TalkBack would announce |
| **Checks** | Structural, visual (contrast), resize, semantic, and journey rules |
| **Judge** | A swappable seam: offline heuristic or any model |
| **Reporters** | Text, JSON, SARIF 2.1.0, each with the conformance profile applied |

See [ARCHITECTURE.md](ARCHITECTURE.md).

## Related work

This project builds on published research rather than claiming to be first:
Latte and Groundhog (assistive-service-driven and crawler-based mobile
accessibility testing) and ScreenAudit (LLM-based screen-reader error
detection). Google's Accessibility Scanner and the Accessibility Test
Framework cover many presence checks on device. A11yJourney's focus is a
developer-first CLI with large-text and semantic checks, a clear line between
required and advisory findings, and an open benchmark.

## Contributing, citing, license

See [CONTRIBUTING.md](CONTRIBUTING.md). If you use A11yJourney in research or
a report, please cite it using [CITATION.cff](CITATION.cff). Licensed under
[MIT](LICENSE).
