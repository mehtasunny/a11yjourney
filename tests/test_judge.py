from a11yjourney import HeuristicJudge, ModelJudge, load, run
from a11yjourney.model import Node

SAMPLE = "examples/sample_login_dump.xml"


def test_heuristic_flags_generic_label():
    j = HeuristicJudge()
    assert j.label_meaningful(Node(cls="Button", desc="Submit payment"), []) is True
    assert j.label_meaningful(Node(cls="Button", desc="button1"), []) is False
    assert j.label_meaningful(Node(cls="ImageView", desc="hero_final_v3.png"), []) is False


def test_model_judge_parses_and_caches():
    calls = {"n": 0}

    def fake_complete(prompt: str) -> str:
        calls["n"] += 1
        # key on the element name line, not the template (which mentions button1)
        return "PASS" if "Sign in" in prompt else "FAIL"

    j = ModelJudge(fake_complete)
    n = Node(cls="Button", desc="button1")
    assert j.label_meaningful(n, []) is False
    assert j.label_meaningful(n, []) is False  # cached
    assert calls["n"] == 1, "identical query should be served from cache"
    assert j.label_meaningful(Node(cls="Button", desc="Sign in"), []) is True


def test_model_judge_falls_back_on_bad_reply():
    j = ModelJudge(lambda _p: "banana")  # not PASS/FAIL
    # falls back to heuristic: a meaningful label still passes
    assert j.label_meaningful(Node(cls="Button", desc="Checkout"), []) is True
    assert j.label_meaningful(Node(cls="Button", desc="btn_1"), []) is False


def test_model_judge_survives_exception():
    def boom(_p: str) -> str:
        raise RuntimeError("network down")

    j = ModelJudge(boom)
    assert j.label_meaningful(Node(cls="Button", desc="Pay now"), []) is True  # heuristic fallback


def test_run_accepts_model_judge():
    findings = run(load(SAMPLE), ModelJudge(lambda _p: "FAIL"))
    assert findings  # a model that fails everything still yields findings
