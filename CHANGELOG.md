# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/), versioning SemVer.

## [0.2.0.dev0] - 2026-09-18
### Added
- Real model support for the semantic judge: `ModelJudge` plus vendor-neutral
  `anthropic_completer` / `openai_completer` adapters and a `make_judge` factory,
  all standard-library only. New `--judge {auto,heuristic,model}` CLI flag.
- Per-element caching and safe fallback so a model error never crashes a run.
- Coverage benchmark: a labeled corpus (ground truth declared independently),
  an evaluator (`a11yjourney.benchmark`), and a runner (`benchmark/run.py`)
  reporting static-only vs full-engine recall and precision.
- Tests for the model judge and the benchmark (13 total).

## [0.1.0] - 2026-09-17
### Added
- Accessibility-tree model and `uiautomator` loader
- Structural, semantic, and journey checks mapped to WCAG 2.2 criteria
- Pluggable `Judge` interface with a dependency-free `HeuristicJudge`
- Text, JSON, and SARIF 2.1.0 reporters
- CLI with severity threshold and CI fail gate
- Test suite, ruff, mypy (strict), and CI
