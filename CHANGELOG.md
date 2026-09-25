# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/), versioning SemVer.

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
