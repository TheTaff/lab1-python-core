import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from labcheck.analyzers import InMemoryAssignmentCatalog
from labcheck.models import AIDeclaration, Assignment, Submission

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
# чтобы в тестах можно было импортировать пример третьего анализатора
sys.path.insert(0, str(ROOT / "examples"))

TEMPLATE = "def main():\n    pass\n"


def make_raw(**changes):
    """Корректная сдача в виде словаря, отдельные поля можно заменить."""
    raw = {
        "submission_id": "s-1",
        "student_id": "student-01",
        "assignment_id": "lab-01",
        "submitted_at": "2026-09-14T18:30:00+03:00",
        "text": "Описание решения.\n\nВторой абзац.",
        "code": "import sys\n\ndef main():\n    pass\n\nprint(sys.argv)\n",
        "ai_declaration": {"used": False, "description": ""},
    }
    raw.update(changes)
    return raw


@pytest.fixture
def raw():
    return make_raw()


@pytest.fixture
def submission():
    return Submission(
        submission_id="s-1",
        student_id="student-01",
        assignment_id="lab-01",
        submitted_at=datetime(2026, 9, 14, 18, 30, tzinfo=timezone(timedelta(hours=3))),
        text="Описание решения.\n\nВторой абзац.",
        code="import sys\n\ndef main():\n    pass\n\nprint(sys.argv)\n",
        ai_declaration=AIDeclaration(used=False),
    )


@pytest.fixture
def catalog():
    return InMemoryAssignmentCatalog(
        [Assignment(assignment_id="lab-01", title="Тестовое", min_lines=3, template=TEMPLATE)]
    )
