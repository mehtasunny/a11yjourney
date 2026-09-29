# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/), versioning SemVer.

## [0.3.1] - 2026-09-29
### Fixed
- `explore` could follow a permission prompt into system settings and tap toggles
  there. It now skips switches, checkboxes, and similar controls, and with
  `--package` never taps anything on another app's screen.
- CITATION.cff no longer carries a DOI field, which kept the 0.3.0 release from
  being archived on Zenodo. The DOI badge in the README is unchanged.

## [0.3.0] - 2026-09-29
### Added
- Keyboard focus measured on the device: `capture --keyboard` presses Tab through
  the screen and records the real focus sequence. Reports focus order (2.4.3),
  controls Tab never reaches (2.1.1), and focus traps (2.1.2). When present, it
  replaces the focus order inferred from the tree.
- Multi-screen capture: `journey` replays a scripted task (launch, tap, type,
  scroll, back, capture); `explore` opens each control on a screen once and
  captures new screens, skipping controls that look consequential.
- `report` audits every capture in a folder, with a combined summary and one
  merged SARIF file.
- Checks that mirror Google's Accessibility Test Framework for any installed
  app: duplicate labels, unclear purpose ("click here", 2.4.4 / 2.4.6), label
  repeating the role, nested duplicate clickable areas, content descriptions on
  editable fields. Platform findings link to the matching ATF check.
- Accuracy tooling: `report --review-sheet` writes findings to a CSV for manual
  verdicts; `score` computes precision and recall per check kind.
- Field study on open-source F-Droid apps (transit, health, government,
  scheduling), run on an emulator by a manual workflow; results publish to the
  `field-study` branch for review.
- README section comparing A11yJourney with ATF, Accessibility Scanner, Compose
  and Espresso checks, Android Studio UI Check, commercial suites, and the
  research it builds on (AccessiText, dVermin, SUDFinder, Latte, Groundhog,
  ScreenAudit).

### Changed
- Findings are de-duplicated per element and criterion.
- Synthetic benchmark: recall 88.9%, precision 66.7% (was 85.2% and 67.6%).

### Fixed (found by the first runs on real apps and the Compose demo)
- List items sharing one resource id were treated as one element, so moving through
  a list with Tab looked like a keyboard trap. Elements are now keyed by id and label.
- A measured Tab cycle that began partway down the screen was read as focus jumping
  up. Cycles are now rotated to start at the first element on screen.
- The Tab walk left the device out of touch mode, so the next app launched with its
  first field focused and the keyboard open. The walk now ends with a harmless tap.
- Contrast was estimated for emoji (such as flags) and for text cut down to a sliver
  behind the keyboard. Both are now skipped and counted in the notes.
- `explore` stopped when Back left the app; it now relaunches the app and continues.
- On one app, `explore` followed a permission prompt into system settings and tapped
  toggles there. It now skips switches, checkboxes, and similar controls, and with
  `--package` it never taps anything on another app's screen.
- The field study processed only the first app, because adb read the rest of the
  list from standard input. adb now gets no standard input.

## [0.2.1] - 2026-09-25
### Fixed
- False positives on Jetpack Compose apps, found by auditing a real Compose app
  on an emulator (fixtures in `tests/fixtures/compose/`). The first run reported
  20 conformance findings on three accessible screens; it now reports none,
  while unlabeled Compose buttons and fields are still caught.
  - Compose puts a button's role on an empty child node; the role now moves to
    the clickable parent that TalkBack focuses, and the parent is named by its
    label text.
  - A text field's label drawn inside it (a child node in Compose) counts as its
    label.
  - Only clickable elements, or focusable controls, count as targets.
  - Elements cut off at the edge of the screen or a scrolling area are no longer
    size-checked (a note says how many were skipped).
  - Visual reading order groups elements into rows, so side-by-side fields of
    different heights are read left to right.
  - Resize check: text pushed off screen at 200% is fine when the screen
    scrolls, and a text box that got wider instead of taller is not "stuck".
- `capture` now reports uiautomator's own error message and retries five times.

## [0.2.0] - 2026-09-25
### Added
- `a11yjourney capture`: one command captures the accessibility tree, a
  screenshot, and the tree again at 200% font scale from a connected device
  over adb. Records screen density and restores the font scale afterwards.
- Contrast checks from screenshots: text (WCAG 1.4.3) and icon controls
  (1.4.11). Standard-library PNG decoder; disabled controls are exempt.
- Resize-text check (WCAG 1.4.4): text that disappears, overlaps, runs off
  screen, or does not grow at 200% font size.
- Conformance profiles. Reports are judged against WCAG 2.1 AA by default (the
  level required by the ADA Title II and HHS Section 504 rules), with
  `--standard wcag22-aa` available. Findings outside the profile are reported
  as advisory and never fail the CI gate.
- WCAG 2.5.8 spacing exception, and target-size findings reported under the
  threshold they actually fail (2.5.8, 2.5.5, or Android's 48dp guidance).
- Redaction of personal data before any text is sent to a model (on by
  default, `--no-redact` to disable). Text typed into fields is never sent.
- Real model support for the semantic judge (`ModelJudge`, Anthropic and
  OpenAI-compatible adapters, `--judge`, `--model`), with caching and a warning
  whenever model calls fail and the heuristic decides instead.
- Coverage benchmark (`benchmark/`, `docs/benchmark.md`) and a field
  validation protocol for real apps (`docs/field-validation.md`).
- Synthetic transit example with screenshot and large-text capture.
- `CITATION.cff`.

### Changed
- Criteria now carry their conformance level and the WCAG version that
  introduced them. v0.1 mapped everything to WCAG 2.2 and reported small
  targets as 2.5.8, which overstated requirements for WCAG 2.1 AA.
- No model names are hard-coded; choose one with `--model` or
  `A11YJOURNEY_MODEL`.
- Unlabeled clickable containers are named by their children, as TalkBack
  reads them, and field hints count as labels. This removes false positives on
  list rows and cards.
- Target sizes are skipped with a note when screen density is unknown
  (previously pixels were silently treated as dp). New `--density` flag.
- Requires Python 3.10+.

## [0.1.0] - 2026-09-17
### Added
- Accessibility-tree model and `uiautomator` loader
- Structural, semantic, and journey checks mapped to WCAG 2.2 criteria
- Pluggable `Judge` interface with a dependency-free `HeuristicJudge`
- Text, JSON, and SARIF 2.1.0 reporters
- CLI with severity threshold and CI fail gate
- Test suite, ruff, mypy (strict), and CI
