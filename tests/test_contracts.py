"""Контрактные тесты: один набор проверок для всех источников и всех анализаторов."""

import copy
import json

import pytest

from labcheck.analyzers import AnalysisContext, LengthAnalyzer, TemplateAnalyzer
from labcheck.models import AnalysisReport, Submission
from labcheck.parser import parse_dict
from labcheck.sources import InMemorySource, JsonlSource

from ai_declaration_analyzer import AIDeclarationAnalyzer
from conftest import make_raw

RAW = [make_raw(), make_raw(submission_id="s-2", code="print(2)\n")]


def make_memory_source(tmp_path):
    return InMemorySource([parse_dict(item) for item in RAW])


def make_jsonl_source(tmp_path):
    path = tmp_path / "subs.jsonl"
    path.write_text("\n".join(json.dumps(item) for item in RAW) + "\n", encoding="utf-8")
    return JsonlSource(path)


@pytest.fixture(params=[make_memory_source, make_jsonl_source], ids=["memory", "jsonl"])
def source(request, tmp_path):
    return request.param(tmp_path)


def test_source_yields_submissions(source):
    with source as items:
        result = list(items)
    assert [s.submission_id for s in result] == ["s-1", "s-2"]
    assert all(isinstance(s, Submission) for s in result)


def test_source_can_be_stopped_early(source):
    with source as items:
        for item in items:
            first = item
            break
    assert first.submission_id == "s-1"


@pytest.fixture(
    params=[LengthAnalyzer, TemplateAnalyzer, AIDeclarationAnalyzer],
    ids=["length", "template", "ai_declaration"],
)
def analyzer(request):
    return request.param()


def test_analyzer_returns_report(analyzer, submission, catalog):
    context = AnalysisContext(catalog.get("lab-01"), catalog)
    report = analyzer.analyze(submission, context)
    assert isinstance(report, AnalysisReport)
    assert report.submission_id == submission.submission_id
    assert report.analyzer_id == analyzer.analyzer_id
    assert report.analyzer_version == analyzer.analyzer_version
    assert report.rubric_feedback


def test_analyzer_does_not_change_submission(analyzer, submission, catalog):
    before = copy.deepcopy(submission)
    analyzer.analyze(submission, AnalysisContext(catalog.get("lab-01"), catalog))
    assert submission == before


def test_analyzer_evidence_inside_content(analyzer, submission, catalog):
    report = analyzer.analyze(submission, AnalysisContext(catalog.get("lab-01"), catalog))
    for item in report.evidence:
        content = submission.text if item.field == "text" else submission.code
        assert 1 <= item.line_start <= item.line_end <= len(content.splitlines())
