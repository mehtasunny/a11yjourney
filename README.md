# A11yJourney

**Journey-based, semantic accessibility auditing for native mobile apps.**

[![ci](https://github.com/mehtasunny/a11yjourney/actions/workflows/ci.yml/badge.svg)](https://github.com/mehtasunny/a11yjourney/actions)
[![python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![license: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Automated accessibility scanners inspect a single screen's accessibility tree
and report what is structurally missing: a missing label, a small touch target,
a contrast failure. Independent analysis has repeatedly shown that this
reliably covers only a small share of the WCAG success criteria. The rest,
close to half, require *judgment*: is a label actually meaningful, does focus
order make sense, can a screen-reader user complete a task across a whole flow.

**A11yJourney targets that gap on native mobile.** It walks an app the way an
assistive-technology user does, combines structural checks with model-based
semantic judgment, and reports the failures static tools cannot see, each
mapped to a specific WCAG criterion.

> **Status: v0.1, early but real.** The engine, the WCAG mapping, JSON and
> SARIF output, and a CI gate all work today. The default semantic judge is a
> dependency-free heuristic; swap in a real model via the `Judge` interface.
> Live on-device capture and the coverage benchmark are on the roadmap.

## Why it exists

Federal and international law now require it. The ADA Title II rule covers state
and local government **web and mobile apps** on a compliance timeline, Section
508 binds federal agencies, and the European Accessibility Act reaches companies
serving EU customers. Teams need to find the accessibility failures that matter,
not just the ones that are easy to detect.

## Install

```bash
pip install -e ".[dev]"     # from a clone
```

## Use

```bash
# human-readable
a11yjourney examples/sample_login_dump.xml

# machine formats
a11yjourney examples/sample_login_dump.xml --format json
a11yjourney examples/sample_login_dump.xml --format sarif > results.sarif

# gate a CI pipeline (non-zero exit on findings)
a11yjourney examples/sample_login_dump.xml --min-severity serious --fail-on-findings
```

The SARIF output uploads directly to GitHub code scanning, so accessibility
findings show up inline on pull requests like any other static-analysis result.

## Semantic judge: heuristic or a real model

The semantic and journey checks run through a swappable `Judge`. The default is
an offline heuristic (no key, no network). To use a real model, set a key and
pass `--judge model` (or `--judge auto`):

```bash
export ANTHROPIC_API_KEY=sk-...        # or OPENAI_API_KEY (any OpenAI-compatible endpoint)
a11yjourney examples/sample_login_dump.xml --judge model
```

Provider calls use only the standard library, results are cached per element,
and a model error or odd reply falls back to the heuristic so a run never
crashes. See `a11yjourney/judge.py`.

## Coverage benchmark

A key claim of this project is measurable: the full engine recovers more of a
screen's genuine accessibility problems than a static-only scanner can. The
`benchmark/` corpus is labeled with ground truth declared independently of the
engine. Run it:

```bash
python benchmark/run.py
```

Seed corpus results (synthetic screens, offline heuristic judge):

| Mode | Recall of genuine issues |
|---|---|
| static-only (presence/absence) | ~59% |
| full engine (heuristic judge) | ~85% |

The gap is the point, and it widens with a real model judge on the
judgment-class criteria. These are seed numbers on synthetic screens; the
roadmap is to grow the corpus with real open-source apps and report model-judge
results. See [docs/benchmark.md](docs/benchmark.md) once populated.

## How it works

| Layer | What it does |
|-------|--------------|
| **Capture** | Read the accessibility tree from a device or emulator. Today, from a `uiautomator dump` XML, the same data TalkBack and Appium use. |
| **Model** | Parse it into typed nodes and compute screen-reader focus order. |
| **Structural checks** | Presence-and-absence rules: labels, target size, inputs. |
| **Semantic + journey checks** | A `Judge` evaluates meaning, focus-order logic, and task completability. Swap `HeuristicJudge` for a real model. |
| **Reporters** | Text, JSON, and SARIF 2.1.0. |

See [ARCHITECTURE.md](ARCHITECTURE.md).

## Related work

This project builds on and cites a serious research base rather than pretending
to be first: Latte and Groundhog (assistive-service-driven and crawler-based
mobile accessibility testing) and ScreenAudit (LLM-based screen-reader error
detection). A11yJourney's focus is a developer-first, CI-native tool plus an
open coverage benchmark for native mobile.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and the [roadmap](CHANGELOG.md). Issues
and pull requests are welcome.

## License

[MIT](LICENSE).
