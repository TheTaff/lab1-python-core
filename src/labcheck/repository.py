"""Хранилище сдач в памяти."""

from labcheck.models import Submission


class InMemorySubmissionRepository:
    def __init__(self) -> None:
        self._items: dict[str, Submission] = {}

    def get(self, submission_id: str) -> Submission | None:
        return self._items.get(submission_id)

    def add(self, submission: Submission) -> None:
        self._items[submission.submission_id] = submission

    def all(self) -> list[Submission]:
        return list(self._items.values())

    def __len__(self) -> int:
        return len(self._items)
