"""Run the coverage benchmark and print + save results."""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))
from a11yjourney.benchmark import aggregate, evaluate_corpus, format_markdown  # noqa: E402
from a11yjourney.judge import make_judge  # noqa: E402

CORPUS = str(pathlib.Path(__file__).parent / "corpus")


def main() -> None:
    judge = make_judge("auto")  # uses a model if a key is set, else heuristic
    results = evaluate_corpus(CORPUS, judge)
    print(format_markdown(results))
    agg = aggregate(results)
    print("\nAggregate:", json.dumps(agg, indent=2))
    out = pathlib.Path(__file__).parent / "results.json"
    out.write_text(json.dumps(
        {"aggregate": agg,
         "cases": [r.__dict__ for r in results]}, indent=2))
    print(f"\nsaved -> {out}")


if __name__ == "__main__":
    main()
