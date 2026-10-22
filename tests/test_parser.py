import copy
import json

import pytest

from labcheck.errors import FormatError, SchemaError
from labcheck.parser import parse_dict, parse_line

from conftest import make_raw


def test_valid_record(raw):
    submission = parse_dict(raw)
    assert submission.submission_id == "s-1"
    assert submission.submitted_at.utcoffset() is not None
    assert submission.ai_declaration.used is False


def test_input_is_not_changed(raw):
    before = copy.deepcopy(raw)
    parse_dict(raw)
    assert raw == before


def test_broken_json_is_format_error():
    with pytest.raises(FormatError) as info:
        parse_line('{"submission_id": "s-1", ')
    assert info.value.code == "invalid_json"


def test_json_list_is_format_error():
    with pytest.raises(FormatError):
        parse_line("[1, 2, 3]")


def test_timestamp_without_timezone():
    with pytest.raises(SchemaError) as info:
        parse_dict(make_raw(submitted_at="2026-09-14T18:30:00"))
    assert info.value.code == "invalid_timestamp"
    assert info.value.field == "submitted_at"
    assert info.value.message


def test_timestamp_not_a_date():
    with pytest.raises(SchemaError) as info:
        parse_dict(make_raw(submitted_at="вчера"))
    assert info.value.code == "invalid_timestamp"


def test_empty_student_id():
    with pytest.raises(SchemaError) as info:
        parse_dict(make_raw(student_id="  "))
    assert info.value.code == "empty_field"
    assert info.value.field == "student_id"


def test_unknown_field():
    with pytest.raises(SchemaError) as info:
        parse_dict(make_raw(grade=5))
    assert info.value.code == "unknown_field"
    assert info.value.field == "grade"


def test_missing_field(raw):
    del raw["code"]
    with pytest.raises(SchemaError) as info:
        parse_dict(raw)
    assert info.value.code == "missing_field"
    assert info.value.field == "code"


@pytest.mark.parametrize(
    "changes, field",
    [
        ({"student_id": 123}, "student_id"),
        ({"code": ["print(1)"]}, "code"),
        ({"ai_declaration": "нет"}, "ai_declaration"),
        ({"ai_declaration": {"used": "yes"}}, "ai_declaration.used"),
        ({"ai_declaration": {"used": True, "description": 1}}, "ai_declaration.description"),
    ],
)
def test_wrong_types(changes, field):
    with pytest.raises(SchemaError) as info:
        parse_dict(make_raw(**changes))
    assert info.value.code == "invalid_type"
    assert info.value.field == field


def test_parse_line_gives_same_result_as_parse_dict(raw):
    assert parse_line(json.dumps(raw)) == parse_dict(raw)
