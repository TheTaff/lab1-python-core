import dataclasses

import pytest

from labcheck.analysis import AnalysisService
from labcheck.analyzers import AnalysisContext, LengthAnalyzer, TemplateAnalyzer
from labcheck.errors import AnalyzerError
from labcheck.models import AnalysisReport, Evidence
from labcheck.registry import default_registry

from ai_declaration_analyzer import AIDeclarationAnalyzer


@pytest.fixture
def context(catalog):
    return AnalysisContext(catalog.get("lab-01"), catalog)


def test_length_counts_non_empty_lines(submission, context):
    report = LengthAnalyzer().analyze(submission, context)
    assert report.score is None
    assert "текст 2, код 4" in report.rubric_feedback[0]


def test_template_finds_exact_lines(submission, context):
    # код: 1 import sys / 2 пусто / 3 def main(): / 4 pass / 5 пусто / 6 print
    report = TemplateAnalyzer().analyze(submission, context)
    assert report.similarity == 0.5
    assert [(e.field, e.line_start, e.line_end) for e in report.evidence] == [("code", 3, 4)]
    assert any("разрешено" in line for line in report.rubric_feedback)
    # номера строк относятся к исходному коду
    lines = submission.code.splitlines()
    assert lines[2:4] == ["def main():", "    pass"]


def test_template_no_match(submission, context):
    other = dataclasses.replace(submission, code="x = 1\ny = 2\n")
    report = TemplateAnalyzer().analyze(other, context)
    assert report.similarity == 0.0
    assert report.evidence == ()


def test_template_empty_code(submission, context):
    report = TemplateAnalyzer().analyze(dataclasses.replace(submission, code=""), context)
    assert report.similarity == 0.0


def test_service_picks_analyzer_by_id(submission, catalog):
    service = AnalysisService(default_registry(), catalog)
    assert service.run("length", submission).analyzer_id == "length"
    assert service.run("template", submission).analyzer_id == "template"


def test_unknown_analyzer(submission, catalog):
    service = AnalysisService(default_registry(), catalog)
    with pytest.raises(AnalyzerError) as info:
        service.run("magic", submission)
    assert info.value.code == "unknown_analyzer"


def test_unknown_assignment(submission, catalog):
    service = AnalysisService(default_registry(), catalog)
    other = dataclasses.replace(submission, assignment_id="lab-99")
    with pytest.raises(AnalyzerError) as info:
        service.run("length", other)
    assert info.value.code == "unknown_assignment"


class BrokenAnalyzer:
    analyzer_id = "broken"
    analyzer_version = "0.1"

    def analyze(self, submission, context):
        raise ZeroDivisionError("упал")


class BadEvidenceAnalyzer:
    analyzer_id = "bad_evidence"
    analyzer_version = "0.1"

    def analyze(self, submission, context):
        return AnalysisReport(
            submission_id=submission.submission_id,
            analyzer_id=self.analyzer_id,
            analyzer_version=self.analyzer_version,
            evidence=(Evidence("code", 1, 999, "за границей"),),
        )


def test_analyzer_failure_becomes_analyzer_error(submission, catalog):
    registry = default_registry()
    registry.register("broken", BrokenAnalyzer)
    with pytest.raises(AnalyzerError) as info:
        AnalysisService(registry, catalog).run("broken", submission)
    assert info.value.code == "analyzer_failed"


def test_evidence_out_of_range_is_rejected(submission, catalog):
    registry = default_registry()
    registry.register("bad_evidence", BadEvidenceAnalyzer)
    with pytest.raises(AnalyzerError) as info:
        AnalysisService(registry, catalog).run("bad_evidence", submission)
    assert info.value.code == "bad_evidence"


def test_third_analyzer_without_changing_service(submission, catalog):
    registry = default_registry()
    registry.register("ai_declaration", AIDeclarationAnalyzer)
    service = AnalysisService(registry, catalog)

    report = service.run("ai_declaration", submission)
    assert "не использовался" in report.rubric_feedback[0]

    declared = dataclasses.replace(
        submission, ai_declaration=dataclasses.replace(submission.ai_declaration, used=True)
    )
    report = service.run("ai_declaration", declared)
    assert "описание пустое" in report.rubric_feedback[0]


def test_registry_rejects_double_registration():
    registry = default_registry()
    with pytest.raises(ValueError):
        registry.register("length", LengthAnalyzer)
