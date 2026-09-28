# A11yJourney

**Accessibility checks for native Android apps, aimed at the health, public
transit, and government apps that new U.S. accessibility rules now cover.**

[![ci](https://github.com/mehtasunny/a11yjourney/actions/workflows/ci.yml/badge.svg)](https://github.com/mehtasunny/a11yjourney/actions)
[![python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23006687.svg)](https://doi.org/10.5281/zenodo.23006687)
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

> **Status: v0.3.0, early.** The checks below work and are covered by tests,
> a small synthetic benchmark, and real Jetpack Compose captures. A study on
> open-source apps is set up but not yet reviewed, so there are no accuracy
> numbers for real apps yet (see [field/README.md](field/README.md)). Until
> then, treat findings as leads to confirm, not verdicts.

## What it checks

| Check | WCAG | What it needs | Who it helps |
|---|---|---|---|
| Controls with no accessible name, fields with no label | 4.1.2, 3.3.2 | tree | screen-reader users |
| Labels that are present but meaningless ("button1", "ic_img_2.png") | 2.4.6, 1.1.1 | tree + judge | screen-reader users |
| Several controls with the same label; "click here", "learn more" | 2.4.6, 2.4.4 | tree | screen-reader users |
| Label repeats the role, nested duplicate targets, description on an editable field | Android guidance (mirrors ATF checks) | tree | screen-reader and switch users |
| Keyboard focus order, controls Tab never reaches, focus traps, **measured on the device** | 2.4.3, 2.1.1, 2.1.2 | `capture --keyboard` | keyboard and switch users |
| Focus order inferred from the tree (when not measured) | 2.4.3 | tree | screen-reader users |
| Text and icon contrast | 1.4.3, 1.4.11 | tree + screenshot | low vision, color blindness, glare |
| Text that disappears, overlaps, or clips at 200% font size | 1.4.4 | tree at normal and 200% text | low vision |
| Touch target size, with the WCAG 2.2 spacing exception | 2.5.8, 2.5.5, Android 48dp | tree | tremor, limited dexterity |

It covers more than one screen: `journey` replays a scripted task and `explore`
opens each control on a screen once and captures where it leads (see below).

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
your font size back when it finishes, even if something fails. Add `--keyboard`
to press Tab through the screen and record the real focus order (20 to 60
seconds).

### More than one screen

```bash
a11yjourney journey steps.txt --out run1     # replay a scripted task
a11yjourney explore --out run2 --keyboard    # open each control once, carefully
a11yjourney report run1                      # audit every capture in a folder
a11yjourney report run1 --format sarif       # one SARIF file for CI
```

A journey script is one step per line:

```
launch com.example.transit/.MainActivity
capture home keyboard
tap "Plan trip"
capture planner
scroll down
capture planner-2
back
```

`explore` taps real controls. It never types, skips controls whose labels suggest
an action with consequences (delete, pay, send, sign out, and similar), and stops
if it cannot get back to where it started. Use a test device and a test account.

Part of the report for the example screen:

```
Judged against WCAG 2.1 Level AA
6 conformance findings  |  5 advisory  |  0 need semantic judgment  |  5 to confirm by hand

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
problems on the screens it captures, and it cannot judge everything that needs a
person, for example whether the captions on a video are accurate. Findings
marked **"estimate, confirm on device"** come from pixels, comparisons, or
heuristics and should be checked with TalkBack or a person before they are
reported as defects.

Keyboard focus is measured on the device, but TalkBack's swipe order is
computed separately by Android and is still approximated from the tree.

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

## Accuracy

**Synthetic benchmark.** `benchmark/` holds a small labeled corpus whose ground
truth is declared independently of the engine (`python benchmark/run.py`). On 4
synthetic screens with 27 labeled issues and the offline heuristic judge,
presence-only checks recover about 59% of the issues and the full engine about
89%, with 67% precision. These numbers say nothing about real apps; see
[docs/benchmark.md](docs/benchmark.md).

**Real apps.** `field/` defines a repeatable study on open-source apps from
F-Droid in transit, health, government, and scheduling, run on an emulator by
`.github/workflows/field-study.yml`. Every finding goes into a review sheet
(`a11yjourney report FOLDER --review-sheet review.csv`) that a person checks on
a device, adding any problem the tool missed; `a11yjourney score` then reports
precision and recall per check. Results will be published once reviewed. Until
then this project makes no accuracy claim about real apps.

## How it works

| Layer | What it does |
|---|---|
| **Capture** | `adb`: `uiautomator dump`, `screencap`, a second dump at font scale 2.0, and optionally a Tab walk that records keyboard focus |
| **Journeys** | Scripted steps or cautious exploration across screens |
| **Model** | Parses the tree into typed nodes; works out what TalkBack would announce, including Compose trees |
| **Checks** | Structural, pattern, visual (contrast), resize, keyboard, semantic, and journey rules |
| **Judge** | A swappable seam: offline heuristic or any model |
| **Reporters** | Text, JSON, SARIF 2.1.0, and review sheets, each with the conformance profile applied |

See [ARCHITECTURE.md](ARCHITECTURE.md).

## How this compares

A11yJourney is not the first tool in this space, and for many teams it should
not be the only one.

- **Google's [Accessibility Test Framework](https://github.com/google/Accessibility-Test-Framework-for-Android)
  (ATF)** is the standard. It runs 14 checks, including clickable spans, text
  sizing units, and duplicate speakable text, inside
  [Espresso](https://developer.android.com/training/testing/espresso/accessibility-checking)
  and, since Compose 1.8,
  [Compose tests](https://developer.android.com/develop/ui/compose/accessibility/testing)
  through `enableAccessibilityChecks()`. It also powers
  [Accessibility Scanner](https://support.google.com/accessibility/android/answer/6376570).
  If you can run instrumented tests, use it. A11yJourney mirrors several ATF
  checks so they appear for any installed app, but ATF sees View internals that a
  captured tree does not.
- **Android Studio's Compose UI Check** renders previews at several font sizes
  and runs ATF on each, inside the IDE.
- **Commercial suites** (Deque axe DevTools Mobile, BrowserStack App
  Accessibility, Evinced, Level Access) are broader, with dashboards, manual
  testing workflows, and in some cases 200% text checks.
  [Microsoft Accessibility Insights for Android](https://github.com/microsoft/accessibility-insights-for-android-service)
  was archived in 2023.
- **Research** comes first on the most interesting ideas here. Comparing screens
  at default and enlarged text was published as
  [AccessiText](https://seal.ics.uci.edu/publications/2022_FSE_AccessiText.pdf)
  (FSE 2022, about 88% precision and 95% recall on 30 apps), along with
  [dVermin](https://arxiv.org/abs/2212.04388) (ASE 2022) and
  [SUDFinder](https://github.com/getgo-nobugs/SUDFinder) (2025). Latte and
  Groundhog drive TalkBack and crawl apps; Xbot drives Accessibility Scanner;
  [ScreenAudit](https://arxiv.org/html/2504.02110v1) (CHI 2025) uses a language
  model over screen-reader transcripts.

What A11yJourney adds is narrower: a free, dependency-free command-line tool that
captures a live device and compares normal and 200% text, measures keyboard focus
on the device, reports against a stated WCAG version with advisory findings kept
separate, writes SARIF for CI, handles Jetpack Compose trees, and redacts personal
data before any model call.

## Companion project

[A11yJourney Compose](https://github.com/mehtasunny/a11yjourney-compose) is the
prevention half: Jetpack Compose components with these checks' concerns built
in (required labels, 48dp targets, errors in words, large-text layouts,
captions). Its CI audits its demo app with this tool on an emulator, and the
captures in `tests/fixtures/compose/` come from that app.

## Contributing, citing, license

See [CONTRIBUTING.md](CONTRIBUTING.md). If you use A11yJourney in research or
a report, please cite it using [CITATION.cff](CITATION.cff). Licensed under
[MIT](LICENSE).
