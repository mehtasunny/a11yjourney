# Architecture

A11yJourney is a small, layered pipeline with one deliberately swappable seam.

```
uiautomator dump (XML)
        |
   model.load()            parse -> typed Node / Screen
        |
   checks.run(screen, judge)
        |   +-- _structural()   presence/absence, mirrors existing scanners
        |   +-- _semantic()     meaning + focus order      -----+
        |   +-- _journey()      task completability        -----+--> Judge
        |
   reporters.to_text | to_json | to_sarif
```

## Design principles

- **Zero required dependencies in the core.** The library parses, checks, and
  reports using only the standard library, so it runs anywhere and is trivial
  to adopt in CI.
- **One swappable seam: the `Judge`.** All semantic intelligence lives behind a
  single `Judge` protocol (`judge.py`). `HeuristicJudge` is the default;
  `ModelJudge` adapts any LLM/VLM via a `complete(prompt) -> str` callable, with
  no vendor lock-in. This is where the product's real value will accrue.
- **Every finding cites a standard.** Findings carry a WCAG criterion id from a
  typed registry (`wcag.py`), so output is auditable, not opinion.
- **Machine-first output.** SARIF 2.1.0 makes findings first-class citizens in
  GitHub code scanning and other tooling.

## Extending

- **New check:** add a function in `checks.py`, map it to a criterion in
  `wcag.py`, and cover it with a test.
- **Real model:** construct `ModelJudge(complete)` and pass it to `run()`.
- **New platform (iOS):** add a loader that produces a `Screen`; the checks and
  reporters are platform-agnostic.
