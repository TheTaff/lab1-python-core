"""Исключения доменного слоя.

У каждой ошибки приёма есть code, field и message, чтобы её можно было
показать пользователю и положить в JSON-отчёт.
"""


class IntakeError(Exception):
    """Базовая ошибка приёма сдачи."""

    def __init__(self, code: str, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.field = field
        self.message = message

    def to_dict(self) -> dict[str, str | None]:
        return {"code": self.code, "field": self.field, "message": self.message}


class FormatError(IntakeError):
    """Строка вообще не является JSON-объектом."""


class SchemaError(IntakeError):
    """JSON разобрался, но поля не соответствуют схеме Submission."""


class ConflictError(IntakeError):
    """Такой submission_id уже есть, но содержимое другое."""


class AnalyzerError(Exception):
    """Ошибка при запуске анализатора."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
