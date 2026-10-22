"""Центральный сервис анализа."""

from labcheck.analyzers import AnalysisContext, AssignmentCatalog, check_report
from labcheck.errors import AnalyzerError
from labcheck.models import AnalysisReport, Submission
from labcheck.registry import AnalyzerRegistry


class AnalysisService:
    def __init__(self, registry: AnalyzerRegistry, catalog: AssignmentCatalog) -> None:
        self.registry = registry
        self.catalog = catalog

    def run(self, analyzer_id: str, submission: Submission) -> AnalysisReport:
        analyzer = self.registry.create(analyzer_id)

        assignment = self.catalog.get(submission.assignment_id)
        if assignment is None:
            raise AnalyzerError(
                "unknown_assignment", f"нет задания {submission.assignment_id}"
            )
        context = AnalysisContext(assignment=assignment, catalog=self.catalog)

        try:
            report = analyzer.analyze(submission, context)
        except AnalyzerError:
            raise
        except Exception as exc:
            # любую поломку анализатора превращаем в понятную ошибку
            raise AnalyzerError(
                "analyzer_failed", f"анализатор {analyzer_id} завершился с ошибкой: {exc}"
            ) from exc

        check_report(report, submission)
        return report
