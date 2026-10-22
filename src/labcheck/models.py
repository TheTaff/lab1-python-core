"""Модели данных. Все dataclass заморожены, чтобы объекты нельзя было случайно изменить."""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class AIDeclaration:
    used: bool
    description: str = ""


@dataclass(frozen=True)
class Submission:
    submission_id: str
    student_id: str
    assignment_id: str
    submitted_at: datetime
    text: str
    code: str
    ai_declaration: AIDeclaration

    @property
    def content_hash(self) -> str:
        """Хеш содержимого сдачи. По нему отличаем дубликат от конфликта."""
        payload = {
            "student_id": self.student_id,
            "assignment_id": self.assignment_id,
            "submitted_at": self.submitted_at.isoformat(),
            "text": self.text,
            "code": self.code,
            "ai_used": self.ai_declaration.used,
            "ai_description": self.ai_declaration.description,
        }
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Assignment:
    assignment_id: str
    title: str
    min_lines: int
    template: str = ""


@dataclass(frozen=True)
class Evidence:
    """Фрагмент исходного содержимого. Номера строк считаются с 1, границы включительно."""

    field: str  # "text" или "code"
    line_start: int
    line_end: int
    note: str


@dataclass(frozen=True)
class AnalysisReport:
    submission_id: str
    analyzer_id: str
    analyzer_version: str
    score: float | None = None
    similarity: float | None = None
    rubric_feedback: tuple[str, ...] = ()
    evidence: tuple[Evidence, ...] = field(default_factory=tuple)
