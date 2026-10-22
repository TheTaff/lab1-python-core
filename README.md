# ЛР 1. Приём работ и расширяемые анализаторы

Траектория: **Python Core**, основной уровень.

Пакет `labcheck` принимает сдачи лабораторных из JSONL, проверяет их и запускает
анализаторы. Принятый код студентов не запускается, он обрабатывается только как текст.

## Установка

Нужен Python 3.11 или новее. Сторонних зависимостей нет, для тестов нужен pytest.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install ".[dev]"
```

## Запуск

```bash
# успешный импорт: 5 сдач принято, 1 дубликат
labcheck import data/submissions.jsonl

# импорт с ошибками: в строке 9 конфликт, остальные ошибки формата и схемы
labcheck import data/invalid_submissions.jsonl

# анализаторы
labcheck analyze data/submissions.jsonl --assignments data/assignments.json --analyzer length
labcheck analyze data/submissions.jsonl --assignments data/assignments.json --analyzer template

# тесты
pytest
```

Вывод `import`:

```json
{"accepted": 5, "duplicate": 1, "errors": []}
```

Каждая ошибка в `errors` содержит `line`, `code`, `field` и `message`.

## Формат сдачи

Одна строка JSONL — одна версия сдачи. Все поля обязательные, лишние поля запрещены.

| Поле | Тип | Проверка |
|---|---|---|
| `submission_id` | строка | не пустая |
| `student_id` | строка | не пустая |
| `assignment_id` | строка | не пустая |
| `submitted_at` | строка | ISO 8601 с временной зоной (`+03:00` или `Z`) |
| `text` | строка | |
| `code` | строка | |
| `ai_declaration` | объект | `used` — true/false, `description` — строка (необязательное) |

Файлы в `data/` придуманы для примера, реальных работ студентов в них нет.

## Устройство

```
src/labcheck/
  models.py      dataclass: Submission, Assignment, AnalysisReport, Evidence
  errors.py      исключения: FormatError, SchemaError, ConflictError, AnalyzerError
  parser.py      разбор JSON и валидация
  repository.py  хранилище в памяти
  intake.py      сервис приёма (дубликаты, конфликты, импорт строк)
  sources.py     источники: JsonlSource и InMemorySource
  analyzers.py   Protocol Analyzer, LengthAnalyzer, TemplateAnalyzer
  registry.py    реестр фабрик анализаторов
  analysis.py    центральный сервис анализа
  cli.py         команды import и analyze
examples/
  ai_declaration_analyzer.py   третий анализатор для защиты
  measure_import.py            замер скорости импорта
```

### Ошибки

| Класс | Когда | Коды |
|---|---|---|
| `FormatError` | строка не JSON-объект | `invalid_json` |
| `SchemaError` | JSON есть, но поля не те | `missing_field`, `unknown_field`, `invalid_type`, `empty_field`, `invalid_timestamp` |
| `ConflictError` | тот же `submission_id`, другое содержимое | `conflict` |

Дубликат (тот же `submission_id` и тот же хеш содержимого) ошибкой не считается:
сервис возвращает уже принятую сдачу. При конфликте старая запись не перезаписывается.
Новая версия работы должна иметь новый `submission_id`.

### Как добавить анализатор

Написать класс с полями `analyzer_id`, `analyzer_version` и методом
`analyze(submission, context)`, затем зарегистрировать его:

```python
from labcheck.registry import default_registry
from ai_declaration_analyzer import AIDeclarationAnalyzer

registry = default_registry()
registry.register("ai_declaration", AIDeclarationAnalyzer)
```

`AnalysisService` при этом не меняется: он берёт анализатор из реестра по
идентификатору и не знает про конкретные классы. Это проверяет тест
`test_third_analyzer_without_changing_service`.
