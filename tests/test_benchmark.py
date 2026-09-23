import pathlib

from a11yjourney.benchmark import aggregate, evaluate_corpus

CORPUS = str(pathlib.Path(__file__).parent.parent / "benchmark" / "corpus")


def test_full_engine_beats_static_only():
    agg = aggregate(evaluate_corpus(CORPUS))
    assert agg["full_recall_pct"] > agg["static_recall_pct"]
    assert agg["ground_truth_issues"] > 0


def test_precision_reasonable():
    agg = aggregate(evaluate_corpus(CORPUS))
    assert agg["full_precision_pct"] >= 60.0
