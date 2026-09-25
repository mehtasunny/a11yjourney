from a11yjourney import ModelJudge, redact
from a11yjourney.model import Node


def test_redacts_common_personal_data():
    s = redact("Jane, DOB 04/12/1961, ID 88213-4471, (206) 555-0142, jane@x.org, "
               "1200 Pine Street")
    for secret in ("1961", "88213", "555", "jane@x.org", "Pine"):
        assert secret not in s
    assert "Jane" in s  # names cannot be caught by patterns; documented limit


def test_keeps_ordinary_ui_text():
    assert redact("Next bus in 5 min") == "Next bus in 5 min"
    assert redact("Route 44") == "Route 44"


def test_model_judge_redacts_by_default_and_can_opt_out():
    seen = []

    def complete(prompt):
        seen.append(prompt)
        return "PASS"

    ModelJudge(complete).label_meaningful(Node(cls="TextView", text="Member 88213-4471"),
                                          ["Call 206-555-0142"])
    assert "88213" not in seen[-1] and "555" not in seen[-1]
    ModelJudge(complete, redact=False).label_meaningful(
        Node(cls="TextView", text="Member 88213-4471"), [])
    assert "88213" in seen[-1]


def test_typed_field_text_never_reaches_the_model():
    from a11yjourney import parse, run
    from conftest import tree
    prompts = []

    def complete(prompt):
        prompts.append(prompt)
        return "PASS"

    xml = tree([
        {"cls": "EditText", "rid": "name", "desc": "Full name", "text": "Jane Q Public",
         "clickable": True, "bounds": (40, 200, 1040, 360)},
        {"cls": "Button", "rid": "submitRow", "clickable": True, "bounds": (0, 400, 1080, 700),
         "children": [{"cls": "EditText", "text": "Jane Q Public",
                       "bounds": (40, 420, 1040, 560)}]},
    ])
    run(parse(xml), ModelJudge(complete))
    assert prompts and not any("Jane Q Public" in p for p in prompts)
