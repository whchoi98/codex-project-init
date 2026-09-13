#!/usr/bin/env python3
"""Create isolated projects for manual/agent skill trials; never run a model."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

SOURCE = '''import argparse
import csv
import json


def summarize(path, column):
    with open(path, newline="", encoding="utf-8") as stream:
        values = [float(row[column]) for row in csv.DictReader(stream)]
    return {"rows": len(values), "total": sum(values)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Summarize one numeric CSV column.")
    parser.add_argument("path")
    parser.add_argument("--column", required=True)
    args = parser.parse_args()
    print(json.dumps(summarize(args.path, args.column)))
'''
REQUESTS = {
    "readme-only": "README만 실제 코드에 맞춰 정리해줘. 기존 운영 메모와 한국어 문체는 유지해줘.",
    "check-only": "이 프로젝트는 README 중심의 문서 구성을 사용해. 파일을 수정하지 말고, "
                  "문서가 코드와 맞는지와 현재 스테이징된 변경의 커밋 준비 상태를 점검해줘.",
    "initialize": "이 CSV 집계 CLI를 다른 개발자가 사용할 수 있도록 Codex 프로젝트 문서를 "
                  "초기화해줘. 새 공개 문서는 영어/한국어로 작성해줘.",
}


def snapshot(project):
    return {p.relative_to(project).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in project.rglob("*") if p.is_file() and not p.is_symlink()}


def create_trials():
    root = Path(tempfile.mkdtemp(prefix="project-init-skill-trials-"))
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
                        "GIT_TERMINAL_PROMPT": "0"})
    for case in REQUESTS:
        project = root / case
        project.mkdir()
        (project / "csv_report.py").write_text(SOURCE, encoding="utf-8")
        (project / "sample.csv").write_text("amount\n2.5\n3.5\n", encoding="utf-8")
        (project / "pyproject.toml").write_text(
            '[project]\nname = "csv-report"\nversion = "0.3.0"\nrequires-python = ">=3.9"\n',
            encoding="utf-8",
        )
        (project / "Makefile").write_text(
            "test:\n\tpython3 -B -m unittest discover -s tests -v\n", encoding="utf-8",
        )
        (project / "tests").mkdir()
        (project / "tests/test_report.py").write_text(
            'import unittest\nfrom csv_report import summarize\n\n'
            'class ReportTests(unittest.TestCase):\n    def test_sample(self):\n'
            '        self.assertEqual(summarize("sample.csv", "amount"), '
            '{"rows": 2, "total": 6.0})\n', encoding="utf-8",
        )
        (project / ".gitignore").write_text("__pycache__/\n*.pyc\n.env\n", encoding="utf-8")
        if case != "initialize":
            (project / "AGENTS.md").write_text(
                "This is a local CSV reporting CLI. Preserve existing document languages "
                "and custom sections. Do not install dependencies or contact remotes.\n",
                encoding="utf-8",
            )
            (project / "README.md").write_text(
                "# CSV 리포트\n\nCSV 숫자 열을 합산합니다. 실행: "
                "`python3 old_report.py sample.csv`.\n\n## 운영 메모\n\n"
                "월말 보고서의 원본 CSV는 수정하지 않습니다. 이 메모는 운영팀이 관리합니다.\n",
                encoding="utf-8",
            )
            (project / "CHANGELOG.md").write_text(
                "# Changelog\n\n## [Unreleased]\n\n## [0.3.0] - 2026-08-20\n\n### Added\n\n"
                "- Preserve operator-provided decimal values in reports.\n", encoding="utf-8",
            )
            (project / "operator-notes.txt").write_text(
                "Owner: reporting team. Keep this manual note exactly.\n", encoding="utf-8",
            )
        if case == "check-only":
            with (project / "README.md").open("a", encoding="utf-8") as stream:
                stream.write("\n[운영 가이드](manual/missing.md)\n\n`--dry-run` 옵션을 지원합니다.\n")
            subprocess.run(["git", "-C", str(project), "init", "-b", "main"],
                           env=environment, capture_output=True, check=True)
            (project / "notes.txt").write_text(
                "-----BEGIN " + "PRIVATE KEY-----\nSYNTHETIC FIXTURE ONLY\n", encoding="utf-8",
            )
            subprocess.run(["git", "-C", str(project), "add", "notes.txt"],
                           env=environment, capture_output=True, check=True)
            (project / "notes.txt").write_text("The worktree content is ordinary text.\n", encoding="utf-8")
        (root / (case + "-before.json")).write_text(
            json.dumps(snapshot(project), indent=2) + "\n", encoding="utf-8",
        )
    return {"root": str(root), "cases": [
        {"path": str(root / case), "request": request} for case, request in REQUESTS.items()
    ]}


if __name__ == "__main__":
    print(json.dumps(create_trials(), ensure_ascii=False, indent=2))
