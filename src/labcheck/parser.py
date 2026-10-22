"""Разбор и валидация сдачи.

Функции ничего не читают из файлов и stdin: на вход строка или словарь,
на выход Submission либо исключение.
"""

import json
from datetime import datetime
from typing import Any

from labcheck.errors import FormatError, SchemaError
from labcheck.models import AIDeclaration, Submission

REQUIRED_FIELDS = (
    "submission_id",
    "student_id",
    "assignment_id",
    "submitted_at",
    "text",
    "code",
    "ai_declaration",
)
# эти поля не могут быть пустыми
ID_FIELDS = ("submission_id", "student_id", "assignment_id")


def parse_line(line: str) -> Submission:
    """Разобрать одну строку JSONL."""
    try:
        data = json.loads(line)
    except json.JSONDecodeError as exc:
        raise FormatError("invalid_json", f"строка не является JSON: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise FormatError("invalid_json", "ожидался JSON-объект")
    return parse_dict(data)


def parse_dict(data: dict[str, Any]) -> Submission:
    """Проверить словарь и собрать из него Submission. Сам словарь не меняется."""
    for name in data:
        if name not in REQUIRED_FIELDS:
            raise SchemaError("unknown_field", f"неизвестное поле {name}", name)
    for name in REQUIRED_FIELDS:
        if name not in data:
            raise SchemaError("missing_field", f"нет обязательного поля {name}", name)

    for name in ("submission_id", "student_id", "assignment_id", "submitted_at", "text", "code"):
        if not isinstance(data[name], str):
            raise SchemaError("invalid_type", f"поле {name} должно быть строкой", name)

    for name in ID_FIELDS:
        if not data[name].strip():
            raise SchemaError("empty_field", f"поле {name} не может быть пустым", name)

    return Submission(
        submission_id=data["submission_id"],
        student_id=data["student_id"],
        assignment_id=data["assignment_id"],
        submitted_at=_parse_timestamp(data["submitted_at"]),
        text=data["text"],
        code=data["code"],
        ai_declaration=_parse_ai_declaration(data["ai_declaration"]),
    )


def _parse_timestamp(value: str) -> datetime:
    try:
        moment = datetime.fromisoformat(value)
    except ValueError as exc:
        raise SchemaError(
            "invalid_timestamp", "submitted_at не в формате ISO 8601", "submitted_at"
        ) from exc
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise SchemaError(
            "invalid_timestamp", "в submitted_at не указана временная зона", "submitted_at"
        )
    return moment


def _parse_ai_declaration(value: Any) -> AIDeclaration:
    name = "ai_declaration"
    if not isinstance(value, dict):
        raise SchemaError("invalid_type", "ai_declaration должно быть объектом", name)
    for key in value:
        if key not in ("used", "description"):
            raise SchemaError("unknown_field", f"неизвестное поле {name}.{key}", f"{name}.{key}")
    if "used" not in value:
        raise SchemaError("missing_field", "нет поля ai_declaration.used", f"{name}.used")
    if not isinstance(value["used"], bool):
        raise SchemaError(
            "invalid_type", "ai_declaration.used должно быть true или false", f"{name}.used"
        )
    description = value.get("description", "")
    if not isinstance(description, str):
        raise SchemaError(
            "invalid_type", "ai_declaration.description должно быть строкой", f"{name}.description"
        )
    return AIDeclaration(used=value["used"], description=description)
