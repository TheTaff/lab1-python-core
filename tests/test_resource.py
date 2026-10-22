"""Проверяем, что JsonlSource закрывает файл в любом случае."""

import json

import pytest

from labcheck.errors import IntakeError
from labcheck.sources import JsonlSource

from conftest import make_raw


@pytest.fixture
def path(tmp_path):
    lines = [
        json.dumps(make_raw()),
        "{битая строка",
        json.dumps(make_raw(submission_id="s-3")),
    ]
    file_path = tmp_path / "subs.jsonl"
    file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return file_path


def test_closed_after_normal_reading(path):
    source = JsonlSource(path)
    with source:
        assert not source.closed
        assert len(list(source.lines())) == 3
    assert source.closed


def test_closed_after_error(path):
    source = JsonlSource(path)
    with pytest.raises(IntakeError):
        with source as items:
            list(items)  # на второй строке будет ошибка
    assert source.closed


def test_closed_after_break(path):
    source = JsonlSource(path)
    with source as items:
        for _ in items:
            break
    assert source.closed


def test_reading_without_with_is_an_error(path):
    with pytest.raises(RuntimeError):
        list(JsonlSource(path).lines())
