"""Замер скорости импорта: python examples/measure_import.py [число строк]"""

import json
import sys
import time

from labcheck.intake import IntakeService
from labcheck.repository import InMemorySubmissionRepository

count = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
lines = [
    json.dumps(
        {
            "submission_id": f"s-{i}",
            "student_id": f"student-{i % 100}",
            "assignment_id": "lab-01",
            "submitted_at": "2026-09-14T18:30:00+03:00",
            "text": "Описание решения.",
            "code": "print(1)\n" * 20,
            "ai_declaration": {"used": False, "description": ""},
        }
    )
    for i in range(count)
]

service = IntakeService(InMemorySubmissionRepository())
start = time.perf_counter()
result = service.import_lines(lines)
elapsed = time.perf_counter() - start
print(f"строк: {count}, принято: {result.accepted}, время: {elapsed:.3f} с")

start = time.perf_counter()
result = service.import_lines(lines)
elapsed = time.perf_counter() - start
print(f"повторный импорт, дубликатов: {result.duplicate}, время: {elapsed:.3f} с")
