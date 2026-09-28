import csv

from a11yjourney.cli import main


def test_review_sheet_and_score(tmp_path, capsys):
    folder = tmp_path / "demoapp"
    folder.mkdir()
    (folder / "login.xml").write_text(open("examples/sample_login_dump.xml").read())
    sheet = tmp_path / "review.csv"
    assert main(["report", str(folder), "--review-sheet", str(sheet)]) in (0, 1)
    capsys.readouterr()
    rows = list(csv.DictReader(sheet.open()))
    assert rows and all(r["verdict"] == "" and r["app"] == "demoapp" for r in rows)

    # a reviewer fills in verdicts and adds one missed issue
    for i, r in enumerate(rows):
        r["verdict"] = "false positive" if i == 0 else "confirmed"
    rows.append({**rows[0], "element": "hidden", "verdict": "missed", "kind": "STRUCTURAL"})
    with sheet.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    assert main(["score", str(sheet), "--format", "json"]) == 0
    import json
    result = json.loads(capsys.readouterr().out)
    n = len(rows) - 1
    assert result["overall"]["confirmed"] == n - 1
    assert result["overall"]["precision_pct"] == round(100 * (n - 1) / n, 1)
    assert result["overall"]["recall_pct"] == round(100 * (n - 1) / n, 1)


def test_score_rejects_unknown_verdicts(tmp_path, capsys):
    sheet = tmp_path / "bad.csv"
    sheet.write_text("app,kind,verdict\nx,STRUCTURAL,maybe\n")
    assert main(["score", str(sheet)]) == 2
    assert "unknown verdict" in capsys.readouterr().err
