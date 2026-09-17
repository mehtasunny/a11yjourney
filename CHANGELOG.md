# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/), versioning follows SemVer.

## [Unreleased]
### Planned
- Live on-device capture via adb and the accessibility APIs
- Real model-backed `Judge` (label meaningfulness, focus-order reasoning)
- iOS accessibility-tree loader
- Coverage benchmark: labeled corpus of human-confirmed failures across real
  open-source apps, with detection-rate comparison vs existing scanners

## [0.1.0] - 2026-09-17
### Added
- Accessibility-tree model and `uiautomator` loader
- Structural, semantic, and journey checks mapped to WCAG 2.2 criteria
- Pluggable `Judge` interface with a dependency-free `HeuristicJudge` and a
  vendor-neutral `ModelJudge` adapter
- Text, JSON, and SARIF 2.1.0 reporters
- CLI with severity threshold and CI fail gate
- Test suite, ruff, mypy (strict), and CI
