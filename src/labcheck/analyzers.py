"""Контракт анализатора и два простых анализатора.

Код сдачи нигде не запускается, он рассматривается только как текст.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from labcheck.errors import AnalyzerError
from labcheck.models import AnalysisReport, Assignment, Evidence, Submission


class AssignmentCatalog(Protocol):
    def get(self, assignment_id: str) -> Assignment | None: ...


class InMemoryAssignmentCatalog:
    def __init__(self, assignments: list[Assignment]) -> None:
        self._items = {a.assignment_id: a for a in assignments}

    def get(self, assignment_id: str) -> Assignment | None:
        return self._items.get(assignment_id)


def load_assignments(path: str | Path) -> InMemoryAssignmentCatalog:
    """Прочитать assignments.json (список объектов)."""
    with open(path, encoding="utf-8") as file:
        raw = json.load(file)
    return InMemoryAssignmentCatalog([Assignment(**item) for item in raw])


@dataclass(frozen=True)
class AnalysisContext:
    """То, что нужно анализатору кроме самой сдачи."""

    assignment: Assignment
    catalog: AssignmentCatalog


class Analyzer(Protocol):
    analyzer_id: str
    analyzer_version: str

    def analyze(self, submission: Submission, context: AnalysisContext) -> AnalysisReport: ...


def count_non_empty(content: str) -> int:
    return sum(1 for line in content.splitlines() if line.strip())


class LengthAnalyzer:
    """Считает непустые строки текста и кода. Оценку не ставит (score=None)."""

    analyzer_id = "length"
    analyzer_version = "1.0"

    def analyze(self, submission: Submission, context: AnalysisContext) -> AnalysisReport:
        text_lines = count_non_empty(submission.text)
        code_lines = count_non_empty(submission.code)
        minimum = context.assignment.min_lines

        feedback = [f"Непустых строк: текст {text_lines}, код {code_lines}."]
        if code_lines < minimum:
            feedback.append(f"Кода меньше, чем требуется в задании (минимум {minimum}).")
        else:
            feedback.append(f"Требование по объёму кода выполнено (минимум {minimum}).")

        return AnalysisReport(
            submission_id=submission.submission_id,
            analyzer_id=self.analyzer_id,
            analyzer_version=self.analyzer_version,
            score=None,
            rubric_feedback=tuple(feedback),
        )


class TemplateAnalyzer:
    """Ищет в коде строки, которые точно совпадают со строками выданного шаблона."""

    analyzer_id = "template"
    analyzer_version = "1.0"

    def analyze(self, submission: Submission, context: AnalysisContext) -> AnalysisReport:
        template_lines = {
            line.strip() for line in context.assignment.template.splitlines() if line.strip()
        }

        # номера строк кода (с 1), совпавших с шаблоном
        matched: list[int] = []
        for number, line in enumerate(submission.code.splitlines(), start=1):
            if line.strip() and line.strip() in template_lines:
                matched.append(number)

        total = count_non_empty(submission.code)
        similarity = len(matched) / total if total else 0.0

        evidence = [
            Evidence("code", start, end, "совпадение с разрешённым шаблоном")
            for start, end in _to_ranges(matched)
        ]
        feedback = [f"Строк, совпавших с шаблоном: {len(matched)} из {total}."]
        if matched:
            feedback.append(
                "Совпадение с шаблоном задания разрешено и не считается заимствованием."
            )

        return AnalysisReport(
            submission_id=submission.submission_id,
            analyzer_id=self.analyzer_id,
            analyzer_version=self.analyzer_version,
            similarity=round(similarity, 3),
            rubric_feedback=tuple(feedback),
            evidence=tuple(evidence),
        )


def _to_ranges(numbers: list[int]) -> list[tuple[int, int]]:
    """[1, 2, 3, 7] -> [(1, 3), (7, 7)]"""
    ranges: list[tuple[int, int]] = []
    for number in numbers:
        if ranges and ranges[-1][1] == number - 1:
            ranges[-1] = (ranges[-1][0], number)
        else:
            ranges.append((number, number))
    return ranges


def check_report(report: AnalysisReport, submission: Submission) -> None:
    """Проверить, что evidence не выходит за границы исходного содержимого."""
    for item in report.evidence:
        content = submission.text if item.field == "text" else submission.code
        last_line = len(content.splitlines())
        if not 1 <= item.line_start <= item.line_end <= last_line:
            raise AnalyzerError(
                "bad_evidence",
                f"evidence {item.line_start}-{item.line_end} вне диапазона 1-{last_line}",
            )
