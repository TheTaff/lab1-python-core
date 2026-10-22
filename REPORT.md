# Отчёт по ЛР 1

**Траектория:** Python Core. **Уровень:** основной.

## Выполненные требования

Этап А:

- пакет в src-layout, устанавливается через `pip install .`;
- модель `Submission` на frozen dataclass;
- разбор JSON и валидация обязательных полей, временной зоны и AI-декларации;
- ошибки с `code`, `field`, `message`; три вида: формат, схема, конфликт;
- дубликат возвращает уже принятую сдачу, конфликт не перезаписывает запись;
- CLI `labcheck import` выводит JSON с `accepted`, `duplicate`, `errors`;
- неверная строка не останавливает импорт и попадает в отчёт с номером строки.

Этап Б:

- контракт `Analyzer` через `Protocol`, метод `analyze(submission, context)`;
- в отчёте есть `analyzer_id` и `analyzer_version`;
- `LengthAnalyzer` и `TemplateAnalyzer`;
- два источника: `JsonlSource` и `InMemorySource`;
- контрактные тесты общие для обоих источников и для всех анализаторов;
- реестр фабрик, в сервисе анализа нет ветвления по классам;
- `JsonlSource` является контекстным менеджером, файл закрывается при ошибке и при `break`;
- третий анализатор (AI-декларация) лежит в `examples/` и подключается без изменения сервиса.

Углублённый уровень не выполнялся.

## Команды проверки

```bash
pip install ".[dev]"
pytest
labcheck import data/submissions.jsonl
labcheck import data/invalid_submissions.jsonl
labcheck analyze data/submissions.jsonl --assignments data/assignments.json --analyzer template
python examples/measure_import.py
```

Результат `pytest`: 52 теста проходят.

Где проверяются обязательные сценарии:

| Сценарий | Тест |
|---|---|
| валидный импорт | `test_cli.py::test_import_valid_file` |
| повреждённый JSON | `test_parser.py::test_broken_json_is_format_error`, `test_intake.py::test_import_continues_after_bad_lines` |
| неверные типы | `test_parser.py::test_wrong_types` |
| дубликат | `test_intake.py::test_duplicate_returns_first_and_does_not_grow` |
| конфликт | `test_intake.py::test_conflict_keeps_original` |
| ошибка анализатора | `test_analyzers.py::test_analyzer_failure_becomes_analyzer_error` |
| освобождение ресурса | `test_resource.py` |
| диапазоны evidence | `test_contracts.py::test_analyzer_evidence_inside_content`, `test_analyzers.py::test_evidence_out_of_range_is_rejected` |
| неизменность исходного объекта | `test_parser.py::test_input_is_not_changed`, `test_contracts.py::test_analyzer_does_not_change_submission` |

## Измерения

Скрипт `examples/measure_import.py`, 10 000 строк, Python 3.13, два запуска:

| Операция | Время |
|---|---|
| первый импорт (все строки новые) | 0,106 с |
| повторный импорт (все строки дубликаты) | 0,30–0,31 с |

Импорт 10 000 сдач занимает около 0,1 с, для учебной группы этого достаточно.
Повторный импорт примерно в три раза медленнее. Причина в том, что хеш содержимого
считается только при совпадении `submission_id`, причём для обеих сдач (старой и
новой), и нигде не сохраняется. Для новых сдач хеш не считается вообще. Это можно
ускорить, если хранить хеш в репозитории рядом со сдачей, но в этой работе я этого не делал.

## Известные ограничения

- данные хранятся только в памяти;
- формат полей `Submission` составлен по тексту задания, файлы в `data/` придуманы;
- сравнение с шаблоном только по точному совпадению строк;
- одно и то же время, записанное в разных зонах, считается разным содержимым.
