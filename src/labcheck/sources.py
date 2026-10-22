"""Источники сдач: файл JSONL и список в памяти.

Оба источника используются одинаково:

    with source as items:
        for submission in items:
            ...
"""

from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import IO, Protocol

from labcheck.models import Submission
from labcheck.parser import parse_line


class SubmissionSource(Protocol):
    def __enter__(self) -> "SubmissionSource": ...

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None: ...

    def __iter__(self) -> Iterator[Submission]: ...


class InMemorySource:
    def __init__(self, submissions: Iterable[Submission]) -> None:
        self._submissions = list(submissions)

    def __enter__(self) -> "InMemorySource":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def __iter__(self) -> Iterator[Submission]:
        return iter(self._submissions)


class JsonlSource:
    """Файл, в котором одна строка = одна сдача.

    Файл открывается в __enter__ и закрывается в __exit__, поэтому он будет
    закрыт и при исключении, и при выходе из цикла по break.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.file: IO[str] | None = None

    def __enter__(self) -> "JsonlSource":
        self.file = self.path.open(encoding="utf-8")
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self.file is not None:
            self.file.close()

    @property
    def closed(self) -> bool:
        return self.file is None or self.file.closed

    def lines(self) -> Iterator[str]:
        """Сырые строки файла, нужны для импорта с отчётом об ошибках."""
        if self.file is None:
            raise RuntimeError("источник нужно открыть через with")
        for line in self.file:
            yield line

    def __iter__(self) -> Iterator[Submission]:
        """Готовые сдачи. На первой же неверной строке бросает IntakeError."""
        for line in self.lines():
            if line.strip():
                yield parse_line(line)
