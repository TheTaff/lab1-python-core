"""Сервис приёма сдач."""

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from labcheck.errors import ConflictError, IntakeError
from labcheck.models import Submission
from labcheck.parser import parse_line
from labcheck.repository import InMemorySubmissionRepository


@dataclass
class ImportResult:
    accepted: int = 0
    duplicate: int = 0
    errors: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"accepted": self.accepted, "duplicate": self.duplicate, "errors": self.errors}


class IntakeService:
    def __init__(self, repository: InMemorySubmissionRepository) -> None:
        self.repository = repository

    def accept(self, submission: Submission) -> tuple[Submission, bool]:
        """Принять сдачу.

        Возвращает (сдача, is_duplicate). Для дубликата возвращается та сдача,
        которая уже лежит в репозитории. При конфликте бросает ConflictError,
        старая запись при этом остаётся как была.
        """
        existing = self.repository.get(submission.submission_id)
        if existing is None:
            self.repository.add(submission)
            return submission, False
        if existing.content_hash == submission.content_hash:
            return existing, True
        raise ConflictError(
            "conflict",
            f"сдача {submission.submission_id} уже принята с другим содержимым",
            "submission_id",
        )

    def import_lines(self, lines: Iterable[str]) -> ImportResult:
        """Импортировать строки JSONL. Плохая строка попадает в errors, импорт идёт дальше."""
        result = ImportResult()
        for number, line in enumerate(lines, start=1):
            if not line.strip():
                continue  # пустые строки просто пропускаем
            try:
                submission = parse_line(line)
                _, is_duplicate = self.accept(submission)
            except IntakeError as exc:
                result.errors.append({"line": number, **exc.to_dict()})
                continue
            if is_duplicate:
                result.duplicate += 1
            else:
                result.accepted += 1
        return result
