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
