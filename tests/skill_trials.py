#!/usr/bin/env python3
"""Create isolated projects for manual/agent skill trials; never run a model."""

import argparse
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
UPDATED_SOURCE = '''import argparse
import csv
import json


def summarize(path, column, delimiter=","):
    with open(path, newline="", encoding="utf-8") as stream:
        values = [float(row[column])
                  for row in csv.DictReader(stream, delimiter=delimiter)
                  if row[column].strip()]
    return {"rows": len(values), "total": sum(values)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Summarize one numeric CSV column.")
    parser.add_argument("path")
    parser.add_argument("--column", required=True)
    parser.add_argument("--delimiter", default=",", help="CSV field separator.")
    parser.add_argument("--pretty", action="store_true", help="Indent the JSON output.")
    args = parser.parse_args()
    report = summarize(args.path, args.column, args.delimiter)
    print(json.dumps(report, indent=2 if args.pretty else None))
'''
EXAMPLE_REMOTE = "https://github.com/example/csv-report.git"
RELEASE_TAG = "v0.3.0"

# These are existing documents, not expected authoring results. In particular,
# the README predates the CLI and one Unreleased translation is behind the other.
BILINGUAL_README = '''# CSV Report

![Python][python-badge] ![Version][version-badge]

# English

## Overview

Summarize a numeric CSV column as JSON. The declared [repository URL][repository]
is an offline example.

## Features

- Read comma-separated exports.
- Stop when a numeric cell is empty.

## Prerequisites

Python 3.8 or later; no external dependencies.

## Installation

Use the local checkout. Run `python3 csv_report.py --help`.

## Usage

```bash
python3 old_report.py sample.csv --field amount
```

```json
{"count": 2, "sum": 6.0}
```

## Operator notes

Month-end source CSVs must stay untouched. The reporting team maintains this note.

## Configuration

Only comma-separated input and compact JSON are supported.

## Project Structure

`csv_report.py` contains the CLI; `sample.csv` is an example input.
Tests live in `tests/`.

## Testing

Run `make test` from the project directory.

## Contributing

Include a sample input and run the declared tests when changing the CLI.

## License

No license has been declared in this repository.

## Contact

The reporting team keeps its local handoff in [operator notes](operator-notes.txt).
No public email or support endpoint has been declared.

# 한국어

## 개요

CSV의 숫자 열을 집계해 JSON으로 출력합니다.
등록된 [저장소 주소][repository]는 오프라인 예시입니다.

## 주요 기능

- 쉼표로 구분된 파일을 읽습니다.
- 숫자 셀이 비어 있으면 실행을 중단합니다.

## 사전 요구 사항

Python 3.8 이상이 필요하며 외부 의존성은 없습니다.

## 설치

로컬 작업 사본에서 `python3 csv_report.py --help`를 실행합니다.

## 사용법

```bash
python3 csv_report.py sample.csv --column amount
```

```json
{"count": 2, "sum": 6.0}
```

## 운영 메모

월말 보고서의 원본 CSV는 수정하지 않습니다. 이 메모는 운영팀이 관리합니다.

## 설정

쉼표로 구분된 입력과 한 줄 JSON 출력만 지원합니다.

## 프로젝트 구조

`csv_report.py`에 CLI가 있으며 `sample.csv`는 예제 입력입니다.
테스트는 `tests/`에 있습니다.

## 테스트

프로젝트 디렉터리에서 `make test`를 실행합니다.

## 기여

CLI를 변경할 때는 예제 입력을 포함하고 프로젝트의 테스트를 실행합니다.

## 라이선스

이 저장소에는 라이선스가 명시되어 있지 않습니다.

## 문의

운영팀의 로컬 인수인계 내용은 [운영 메모](operator-notes.txt)에 있습니다.
공개 이메일이나 지원 창구는 명시되어 있지 않습니다.

[python-badge]: https://img.shields.io/badge/Python-3.8%2B-blue
[version-badge]: https://img.shields.io/badge/version-0.3.0-blue
[repository]: https://github.com/example/csv-report
'''
ENGLISH_HISTORY = '''## [0.3.0] - 2026-08-20

### Added

- Preserve operator-provided decimal values in reports.

### Changed

- Read local CSV files as UTF-8.

## 0.2.0 - 2026-08-01

### Fixed

- Include every data row when computing the total.

'''
KOREAN_HISTORY = '''## [0.3.0] - 2026-08-20

### Added

- 운영자가 입력한 소수 값을 보고서에 유지합니다.

### Changed

- 로컬 CSV 파일을 UTF-8로 읽습니다.

## 0.2.0 - 2026-08-01

### Fixed

- 합계를 계산할 때 모든 데이터 행을 포함합니다.

'''
ENGLISH_ADDITIONS = '''### Added

- Support custom CSV separators with `--delimiter`.
- Offer indented JSON output with `--pretty`.

'''
KOREAN_ADDITIONS = '''### Added

- `--delimiter`로 CSV 구분자를 선택할 수 있습니다.
- `--pretty`로 들여쓴 JSON을 출력합니다.

'''
ENGLISH_FIX = '''### Fixed

- Ignore blank numeric cells when counting rows and computing totals.

'''
KOREAN_FIX = '''### Fixed

- 행 수와 합계를 계산할 때 비어 있는 숫자 셀을 건너뜁니다.

'''
REQUESTS = {
    "readme-only": "README만 실제 코드에 맞춰 정리해줘. 기존 운영 메모와 한국어 문체는 유지해줘.",
    "check-only": "이 프로젝트는 README 중심의 문서 구성을 사용해. 파일을 수정하지 말고, "
                  "문서가 코드와 맞는지와 현재 스테이징된 변경의 커밋 준비 상태를 점검해줘.",
    "initialize": "이 CSV 집계 CLI를 다른 개발자가 사용할 수 있도록 Codex 프로젝트 문서를 "
                  "초기화해줘. 새 공개 문서는 영어/한국어로 작성해줘.",
    "bilingual-sync": "최근 CSV 리포트 CLI 변경 뒤 문서가 뒤처졌어. README와 CHANGELOG를 "
                      "현재 코드에 맞게 동기화해줘.",
    "changelog-release": "CSV 리포트 0.4.0 릴리스 노트를 2026-09-15 날짜로 준비해줘. "
                         "이번 배포에는 구분자 선택과 빈 숫자 셀 처리만 포함하고, "
                         "JSON 들여쓰기는 다음으로 미룰게. CHANGELOG만 정리해줘.",
}


def bilingual_changelog(english="", korean=""):
    return (
        "# Changelog\n\n# English\n\n"
        "The format follows [Keep a Changelog][keep-a-changelog].\n\n"
        "## [Unreleased]\n\n" + english + ENGLISH_HISTORY
        + "# 한국어\n\n"
        "이 문서는 [Keep a Changelog][keep-a-changelog] 형식을 따릅니다.\n\n"
        "## [Unreleased]\n\n" + korean + KOREAN_HISTORY
        + "[keep-a-changelog]: https://keepachangelog.com/en/1.1.0/\n"
        "[Unreleased]: https://github.com/example/csv-report/compare/v0.3.0...HEAD\n"
        "[0.3.0]: https://github.com/example/csv-report/releases/tag/v0.3.0\n"
    )


def git(project, *arguments, date="2026-09-10T12:00:00+0000"):
    # Inherit no identity, credential, Git configuration, or transport variables.
    environment = {key: os.environ[key] for key in ("PATH", "SYSTEMROOT")
                   if key in os.environ}
    environment.update({
        "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_ATTR_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0",
        "GIT_OPTIONAL_LOCKS": "0", "LC_ALL": "C", "TZ": "UTC",
        "GIT_AUTHOR_NAME": "Skill Trial Fixture",
        "GIT_AUTHOR_EMAIL": "skill-trials@example.invalid",
        "GIT_COMMITTER_NAME": "Skill Trial Fixture",
        "GIT_COMMITTER_EMAIL": "skill-trials@example.invalid",
        "GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date,
    })
    return subprocess.run(
        ["git", "-c", "core.hooksPath=" + os.devnull, "-c", "credential.helper=",
         "-c", "protocol.allow=never", "-C", str(project), *arguments],
        env=environment, capture_output=True, text=True, check=True, timeout=15,
    ).stdout.strip()


def initialize_git(project):
    git(project, "init", "--quiet", "--template=", "-b", "main")
    for key, value in (
        ("user.name", "Skill Trial Fixture"),
        ("user.email", "skill-trials@example.invalid"),
        ("user.useConfigOnly", "true"),
        ("commit.gpgSign", "false"),
        ("tag.gpgSign", "false"),
        ("core.hooksPath", os.devnull),
        ("core.autocrlf", "false"),
        ("credential.helper", ""),
        ("protocol.allow", "never"),
    ):
        git(project, "config", "--local", key, value)


def create_history_trial(project, case):
    (project / "README.md").write_text(BILINGUAL_README, encoding="utf-8")
    (project / "CHANGELOG.md").write_text(bilingual_changelog(), encoding="utf-8")
    with (project / "AGENTS.md").open("a", encoding="utf-8") as stream:
        stream.write("The GitHub origin is an offline documentation example, "
                     "not a verified hosting or support service.\n")
    initialize_git(project)
    # remote add only writes local config. There are no transport commands here.
    git(project, "remote", "add", "origin", EXAMPLE_REMOTE)
    git(project, "add", ".")
    git(project, "commit", "--quiet", "-m", "Record the 0.3.0 CSV reporting release",
        date="2026-08-20T12:00:00+0000")
    git(project, "tag", RELEASE_TAG)

    (project / "csv_report.py").write_text(UPDATED_SOURCE, encoding="utf-8")
    (project / "sample-semicolon.csv").write_text(
        "amount;label\n2.5;first\n;missing\n3.5;last\n", encoding="utf-8",
    )
    with (project / "tests/test_report.py").open("a", encoding="utf-8") as stream:
        stream.write(
            '\n    def test_delimiter_and_blank_cells(self):\n'
            '        self.assertEqual(summarize("sample-semicolon.csv", "amount", ";"), '
            '{"rows": 2, "total": 6.0})\n',
        )
    if case == "bilingual-sync":
        changelog = bilingual_changelog(
            ENGLISH_ADDITIONS,
            "### Added\n\n- `--pretty`로 들여쓴 JSON을 출력합니다.\n\n",
        )
    else:
        changelog = bilingual_changelog(
            ENGLISH_ADDITIONS + ENGLISH_FIX, KOREAN_ADDITIONS + KOREAN_FIX,
        )
    (project / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
    git(project, "add", ".")
    git(project, "commit", "--quiet", "-m",
        "Add delimiter and pretty output options; skip blank numeric cells")


def snapshot(project):
    return {p.relative_to(project).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(project.rglob("*")) if p.is_file() and not p.is_symlink()}


def metadata_snapshot(project):
    """Read only the standalone trial's Git state and version authority."""
    files = snapshot(project)
    metadata = {"version_files": {"pyproject.toml": files.get("pyproject.toml")},
                "git": None}
    git_dir = project / ".git"
    if git_dir.is_symlink() or (git_dir.exists() and not git_dir.is_dir()):
        raise ValueError("Snapshots support standalone trial repositories only")
    if git_dir.is_dir():
        metadata["git"] = {
            "head": (git_dir / "HEAD").read_text(encoding="utf-8").strip(),
            "refs": dict(line.split("\t") for line in git(
                project, "for-each-ref", "--format=%(refname)\t%(objectname)",
            ).splitlines()),
            "index_sha256": files.get(".git/index"),
            "index_entries": git(project, "ls-files", "--stage").splitlines(),
            "config_sha256": files.get(".git/config"),
            "remotes": git(project, "remote", "-v").splitlines(),
        }
    return metadata


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def create_trials():
    root = Path(tempfile.mkdtemp(prefix="project-init-skill-trials-"))
    cases = []
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
            initialize_git(project)
            (project / "notes.txt").write_text(
                "-----BEGIN " + "PRIVATE KEY-----\nSYNTHETIC FIXTURE ONLY\n", encoding="utf-8",
            )
            git(project, "add", "notes.txt")
            (project / "notes.txt").write_text("The worktree content is ordinary text.\n", encoding="utf-8")
        if case in ("bilingual-sync", "changelog-release"):
            create_history_trial(project, case)
        files_before = root / (case + "-before.json")
        metadata_before = root / (case + "-metadata-before.json")
        write_json(files_before, snapshot(project))
        write_json(metadata_before, metadata_snapshot(project))
        cases.append({"name": case, "path": str(project), "request": REQUESTS[case],
                      "files_before": str(files_before),
                      "metadata_before": str(metadata_before)})
    report = {"root": str(root), "cases": cases}
    write_json(root / "trials.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, metavar="PROJECT",
                        help="Print hashes and local metadata for a generated trial; do not edit it.")
    args = parser.parse_args()
    if args.snapshot:
        if not args.snapshot.is_dir():
            parser.error("--snapshot requires an existing trial directory")
        report = {"files": snapshot(args.snapshot),
                  "metadata": metadata_snapshot(args.snapshot)}
    else:
        report = create_trials()
    print(json.dumps(report, ensure_ascii=False, indent=2))
