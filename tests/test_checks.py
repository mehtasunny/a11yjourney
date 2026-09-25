import os

from a11yjourney import Severity, load, run, summarize

SAMPLE = os.path.join(os.path.dirname(__file__), "..", "examples", "sample_login_dump.xml")


def test_finds_issues_beyond_static():
    findings = run(load(SAMPLE))
    s = summarize(findings)
    assert s["total"] > 0
    assert s["beyond_static"] > 0, "the core thesis: catch what static scanners cannot"


def test_journey_block_is_critical():
    findings = run(load(SAMPLE))
    assert any(f.kind == "JOURNEY" and f.severity is Severity.CRITICAL for f in findings)


def test_every_finding_maps_to_wcag():
    for f in run(load(SAMPLE)):
        assert f.wcag and f.message and f.element


def test_clickable_row_is_named_by_its_children():
    from a11yjourney import parse
    from conftest import tree
    xml = tree([{"cls": "LinearLayout", "rid": "row", "clickable": True,
                 "bounds": (0, 300, 1080, 480),
                 "children": [{"text": "Dr. Patel", "bounds": (40, 320, 600, 380)},
                              {"text": "Tue 3:00 PM", "bounds": (40, 390, 600, 450)}]}])
    findings = run(parse(xml))
    assert not [f for f in findings if f.element == "row" and f.wcag == "4.1.2"]


def test_hint_counts_as_a_field_label():
    from a11yjourney import parse
    from conftest import tree
    xml = tree([{"cls": "EditText", "rid": "q", "clickable": True,
                 "bounds": (40, 300, 1040, 460)}])
    xml = xml.replace('resource-id="org.example:id/q"',
                      'resource-id="org.example:id/q" hint="Search stops"')
    assert not [f for f in run(parse(xml)) if f.wcag == "3.3.2"]
