"""Командная строка.

    labcheck import data/submissions.jsonl
    labcheck analyze data/submissions.jsonl --assignments data/assignments.json --analyzer length
"""

import argparse
import json
import sys
from dataclasses import asdict
from typing import Any

from labcheck.analysis import AnalysisService
from labcheck.analyzers import load_assignments
from labcheck.errors import AnalyzerError
from labcheck.intake import IntakeService
from labcheck.registry import default_registry
from labcheck.repository import InMemorySubmissionRepository
from labcheck.sources import JsonlSource


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="labcheck")
    commands = parser.add_subparsers(dest="command", required=True)

    import_cmd = commands.add_parser("import", help="импортировать сдачи из JSONL")
    import_cmd.add_argument("file")

    analyze_cmd = commands.add_parser("analyze", help="импортировать и проанализировать сдачи")
    analyze_cmd.add_argument("file")
    analyze_cmd.add_argument("--assignments", required=True)
    analyze_cmd.add_argument("--analyzer", required=True, choices=default_registry().ids())
    return parser


def run_import(path: str) -> tuple[IntakeService, dict[str, Any]]:
    service = IntakeService(InMemorySubmissionRepository())
    with JsonlSource(path) as source:
        result = service.import_lines(source.lines())
    return service, result.to_dict()


def run_analyze(path: str, assignments_path: str, analyzer_id: str) -> dict[str, Any]:
    intake, output = run_import(path)
    analysis = AnalysisService(default_registry(), load_assignments(assignments_path))

    reports = []
    analysis_errors = []
    for submission in intake.repository.all():
        try:
            reports.append(asdict(analysis.run(analyzer_id, submission)))
        except AnalyzerError as exc:
            analysis_errors.append(
                {
                    "submission_id": submission.submission_id,
                    "code": exc.code,
                    "message": exc.message,
                }
            )
    output["reports"] = reports
    output["analysis_errors"] = analysis_errors
    return output


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "import":
            _, output = run_import(args.file)
        else:
            output = run_analyze(args.file, args.assignments, args.analyzer)
    except OSError as exc:
        print(f"не удалось прочитать файл: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
