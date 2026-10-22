"""Третий анализатор для защиты.

Проверяет, что при ai_declaration.used = true описание не пустое.
Подключается одной строкой, центральный сервис не меняется:

    registry.register("ai_declaration", AIDeclarationAnalyzer)
"""

from labcheck.analyzers import AnalysisContext
from labcheck.models import AnalysisReport, Submission


class AIDeclarationAnalyzer:
    analyzer_id = "ai_declaration"
    analyzer_version = "1.0"

    def analyze(self, submission: Submission, context: AnalysisContext) -> AnalysisReport:
        declaration = submission.ai_declaration
        if not declaration.used:
            feedback = "ИИ не использовался, описание не требуется."
        elif declaration.description.strip():
            feedback = "Использование ИИ описано."
        else:
            feedback = "Указано использование ИИ, но описание пустое."
        return AnalysisReport(
            submission_id=submission.submission_id,
            analyzer_id=self.analyzer_id,
            analyzer_version=self.analyzer_version,
            rubric_feedback=(feedback,),
        )
