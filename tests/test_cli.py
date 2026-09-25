import json
import pathlib

from a11yjourney.cli import main

ROOT = pathlib.Path(__file__).parent.parent
TRIP = str(ROOT / "examples" / "transit" / "trip.xml")
LOGIN = str(ROOT / "examples" / "sample_login_dump.xml")


def _json(capsys, *args):
    assert main([*args, "--format", "json"]) in (0, 1)
    return json.loads(capsys.readouterr().out)


def test_auto_discovers_screenshot_and_large_text(capsys):
    data = _json(capsys, TRIP)
    ids = {f["wcag"] for f in data["findings"]}
    assert {"1.4.3", "1.4.11", "1.4.4", "3.3.2"} <= ids
    assert any("screenshot" in n for n in data["notes"])


def test_tree_only_ignores_siblings(capsys):
    data = _json(capsys, TRIP, "--tree-only")
    assert not {"1.4.3", "1.4.4"} & {f["wcag"] for f in data["findings"]}


def test_gate_ignores_advisory_findings(tmp_path, capsys):
    xml = ('<?xml version="1.0"?><hierarchy density="3.0">'
           '<node class="android.widget.FrameLayout" bounds="[0,0][1080,2160]">'
           '<node class="android.widget.ImageButton" content-desc="Close" clickable="true" '
           'resource-id="x:id/close" bounds="[500,500][560,560]"/></node></hierarchy>')
    p = tmp_path / "s.xml"
    p.write_text(xml)
    assert main([str(p), "--fail-on-findings"]) == 0  # only 2.5.5 (AAA): advisory
    capsys.readouterr()


def test_standard_flag_changes_scope(capsys):
    d21 = _json(capsys, TRIP, "--tree-only")
    d22 = _json(capsys, TRIP, "--tree-only", "--standard", "wcag22-aa")
    assert d21["profile"]["wcag"] == "2.1" and d22["profile"]["wcag"] == "2.2"


def test_login_gate_fails_on_conformance_findings(capsys):
    assert main([LOGIN, "--fail-on-findings"]) == 1
    capsys.readouterr()


def test_model_judge_without_model_is_a_clean_error(monkeypatch, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    monkeypatch.delenv("A11YJOURNEY_MODEL", raising=False)
    assert main([LOGIN, "--judge", "model"]) == 2
    assert "model name" in capsys.readouterr().err


def test_capture_without_adb_is_a_clean_error(tmp_path, capsys):
    rc = main(["capture", "--name", "x", "--out", str(tmp_path), "--adb", "no-such-adb-binary"])
    assert rc == 2
    assert "platform-tools" in capsys.readouterr().err


def test_sarif_marks_advisory_as_note(capsys):
    assert main([TRIP, "--format", "sarif"]) in (0, 1)
    doc = json.loads(capsys.readouterr().out)
    levels = {r["ruleId"]: r["level"] for r in doc["runs"][0]["results"]}
    assert levels["WCAG-2.5.5"] == "note"
    assert levels["WCAG-3.3.2"] == "error"
