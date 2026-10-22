import json

from labcheck.cli import main

from conftest import DATA


def test_import_valid_file(capsys):
    code = main(["import", str(DATA / "submissions.jsonl")])
    output = json.loads(capsys.readouterr().out)
    assert code == 0
    assert output == {"accepted": 5, "duplicate": 1, "errors": []}


def test_import_invalid_file(capsys):
    main(["import", str(DATA / "invalid_submissions.jsonl")])
    output = json.loads(capsys.readouterr().out)
    assert output["accepted"] == 2
    assert output["duplicate"] == 0
    codes = {e["line"]: e["code"] for e in output["errors"]}
    assert codes == {
        2: "invalid_json",
        3: "invalid_timestamp",
        4: "empty_field",
        5: "unknown_field",
        6: "invalid_type",
        7: "invalid_timestamp",
        8: "missing_field",
        9: "conflict",
    }
    for error in output["errors"]:
        assert set(error) == {"line", "code", "field", "message"}


def test_analyze(capsys):
    main(
        [
            "analyze",
            str(DATA / "submissions.jsonl"),
            "--assignments",
            str(DATA / "assignments.json"),
            "--analyzer",
            "template",
        ]
    )
    output = json.loads(capsys.readouterr().out)
    assert len(output["reports"]) == 5
    assert output["analysis_errors"] == []
    assert all(r["analyzer_id"] == "template" for r in output["reports"])


def test_missing_file(capsys):
    assert main(["import", "no_such_file.jsonl"]) == 2
    assert "не удалось прочитать" in capsys.readouterr().err
