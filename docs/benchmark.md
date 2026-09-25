# Coverage benchmark

The benchmark asks one question: of the accessibility problems a careful
human auditor would confirm on a screen, how many does each mode of the tool
find?

* **Presence-only mode** counts only STRUCTURAL findings (missing names,
  missing field labels, small targets). This is roughly what presence-based
  scanners report.
* **Full engine** counts every finding: structural, semantic, and journey.

## Method

Each case in `benchmark/corpus/` is a screen (`NAME.xml`) plus ground truth
(`NAME.expected.json`): a list of `(element, WCAG criterion)` pairs. Ground
truth is declared by hand in `benchmark/build_corpus.py`, independently of the
engine's code, so the benchmark does not just echo the engine back at itself.

Matching is by element and criterion. Small-target defects are matched as one
family ("target size"), because the engine reports them under whichever
threshold they fail: WCAG 2.2's 2.5.8, WCAG 2.1's 2.5.5, or Android's 48dp
guidance.

```
recall    = labeled issues found / all labeled issues
precision = labeled issues found / all issues reported
```

Run it with `python benchmark/run.py`. Results are written to
`benchmark/results.json`.

## Current results (seed corpus)

Offline heuristic judge, 4 synthetic screens, 27 labeled issues:

| Screen | Labeled issues | Presence-only recall | Full-engine recall |
|---|---|---|---|
| checkout | 7 | 57.1% | 57.1% |
| login | 11 | 63.6% | 100.0% |
| player | 4 | 50.0% | 100.0% |
| settings | 5 | 60.0% | 80.0% |
| **all** | **27** | **59.3%** | **85.2%** |

Full-engine precision on the same corpus is 67.6%.

## Limits, stated plainly

* The screens are synthetic and small, and the same person wrote the checks
  and the ground truth. The results show the method works end to end; they
  do not show how the tool does on real apps.
* The contrast and resize checks need screenshots and paired captures, which
  the seed corpus does not include yet. They are covered by unit tests and the
  synthetic example in `examples/transit/`.
* The checkout case shows two real gaps. The heuristic judge passes a vague
  label ("click here") that a person would fail; a model judge is expected to
  do better, but that has not been measured yet. And the focus-order check
  names the first element reached out of order (`cardNumber`), while the
  ground truth names the element that is misplaced ("Enter payment details"),
  so a real defect is found but scored as a miss.

Real-app results will be reported separately, following
[field-validation.md](field-validation.md), and will not be mixed into these
numbers.
