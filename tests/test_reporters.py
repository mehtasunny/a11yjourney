import json
import os

from a11yjourney import load, run, to_json, to_sarif, to_text

SAMPLE = os.path.join(os.path.dirname(__file__), "..", "examples", "sample_login_dump.xml")


def test_text_report():
    assert "A11yJourney report" in to_text(SAMPLE, run(load(SAMPLE)))


def test_json_is_valid():
    data = json.loads(to_json(SAMPLE, run(load(SAMPLE))))
    assert data["summary"]["total"] == len(data["findings"])


def test_sarif_shape():
    doc = json.loads(to_sarif(SAMPLE, run(load(SAMPLE))))
    assert doc["version"] == "2.1.0"
    assert doc["runs"][0]["tool"]["driver"]["name"] == "A11yJourney"
    assert doc["runs"][0]["results"]
