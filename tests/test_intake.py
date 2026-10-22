import json

import pytest

from labcheck.errors import ConflictError
from labcheck.intake import IntakeService
from labcheck.parser import parse_dict
from labcheck.repository import InMemorySubmissionRepository

from conftest import make_raw


@pytest.fixture
def service():
    return IntakeService(InMemorySubmissionRepository())


def test_accept_new(service, submission):
    accepted, is_duplicate = service.accept(submission)
    assert accepted is submission
    assert not is_duplicate
    assert len(service.repository) == 1


def test_duplicate_returns_first_and_does_not_grow(service):
    first = parse_dict(make_raw())
    second = parse_dict(make_raw())  # другой объект с тем же содержимым
    service.accept(first)
    returned, is_duplicate = service.accept(second)
    assert is_duplicate
    assert returned is first
    assert len(service.repository) == 1


def test_conflict_keeps_original(service):
    first = parse_dict(make_raw())
    service.accept(first)
    with pytest.raises(ConflictError) as info:
        service.accept(parse_dict(make_raw(code="print('другое')")))
    assert info.value.code == "conflict"
    assert info.value.field == "submission_id"
    assert service.repository.get("s-1") is first
    assert len(service.repository) == 1


def test_new_version_has_new_id(service):
    service.accept(parse_dict(make_raw()))
    service.accept(parse_dict(make_raw(submission_id="s-2", code="print(2)")))
    assert len(service.repository) == 2


def test_import_continues_after_bad_lines(service):
    lines = [
        json.dumps(make_raw()),
        "{это не json",
        json.dumps(make_raw(submission_id="s-2", student_id="")),
        "",
        json.dumps(make_raw(submission_id="s-3")),
        json.dumps(make_raw()),  # дубликат первой
        json.dumps(make_raw(text="другой текст")),  # конфликт с первой
    ]
    result = service.import_lines(lines)
    assert result.accepted == 2
    assert result.duplicate == 1
    assert [(e["line"], e["code"]) for e in result.errors] == [
        (2, "invalid_json"),
        (3, "empty_field"),
        (7, "conflict"),
    ]
    assert len(service.repository) == 2
