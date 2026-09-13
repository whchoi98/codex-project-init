# Skill behavior trials

<a href="#english">English</a> · <a href="#korean">한국어</a>

<a id="english"></a>
## English

Python tests validate the helpers. Skill changes also need realistic authoring
and review trials: metadata validation alone cannot prove scope preservation,
semantic accuracy, or repeated-run behavior. Review the authored results, not
whether skill prose contains particular words or headings.

### Generate and isolate

Use Python 3.9 or later and local Git. From the repository root, run:

```bash
python3 -B tests/skill_trials.py
```

The [generator](../../tests/skill_trials.py) creates fresh temporary projects,
prints their paths and realistic user requests, and saves the same manifest as
`trials.json` beside them. It does not invoke a model or execute the projects.
Each project contains a standard-library CSV CLI, example data, and tests.
`CASE-before.json` contains file hashes, including local Git files where present;
`CASE-metadata-before.json` records the version-file hash and local Git HEAD,
refs, index hash/entries, config hash, and remote URLs.

The original `readme-only` and `initialize` cases have no Git repository. The
`check-only` case retains an unborn local repository with a synthetic private-key
header staged in its index; the working-tree replacement is ordinary text.

`bilingual-sync` and `changelog-release` are independent, initially clean local
repositories. Each has a `main` branch, a `v0.3.0` release tag, and a later commit
with CLI changes. `pyproject.toml` still declares `0.3.0`. Setup uses a synthetic
fixture identity, fixed commit dates, an empty Git template, disabled hooks and
signing, isolated configuration, and disabled credential helpers/transports.
The declared origin, `https://github.com/example/csv-report.git`, is an offline
example, not evidence that a hosted repository or support service exists.
Creating these local fixture commits/tags is setup, not part of document
preparation. No remote is contacted and no real credentials are used.

Use the source skill at `skills/project-init/SKILL.md` in a fresh agent context
for each printed request. Give it only that request and the raw project; keep
this guide and the snapshots outside the agent's context. Restrict writes to
the paths in the table below, and run offline with no install, fetch, push, or
remote-link/badge retrieval. Set `GIT_OPTIONAL_LOCKS=0` for trial commands to avoid
incidental index refreshes. The synthetic Git email is fixture metadata, not a
project contact. Inspect the resulting files and output afterward.

| Trial | Write scope | Evidence to verify afterward |
|---|---|---|
| `readme-only` | `README.md` | Correct entrypoint, required `--column`, and sample output; custom Korean operator note and released changelog preserved; unrelated files unchanged |
| `check-only` | None | Broken local link, unsupported option, wrong command, and index-only key header identified; no matching secret value disclosed; all file/index hashes unchanged; project tests not run |
| `initialize` | Applicable project documents | Useful English/Korean docs from the CLI; original application files retained; no fabricated service, license, release history, or Git setup |
| `bilingual-sync` | `README.md`, `CHANGELOG.md` | Stale README facts corrected in both languages; custom operator text and released history preserved; incomplete Unreleased translation reconciled without duplicate entries; stable second sync |
| `changelog-release` | `CHANGELOG.md` | Only selected Unreleased entries moved into the supplied version/date in both languages; deferred entry and older history retained; README, project version, and all Git metadata unchanged |

### Review the requested default format

Apply the [README](../../skills/project-init/references/readme.md) and
[CHANGELOG](../../skills/project-init/references/changelog.md) contracts to new
documents or explicitly requested format adoption. The existing Korean-only
and custom bilingual fixtures retain their established headings, notes, and
layout; compare their content roles and paired facts without forcing conversion.

- New README files have the license, build, version, and language badge row;
  new changelogs have language badges. Images use `img.shields.io`, and language
  links target `#english` and `#한국어`. Unknown license/build information uses
  the guide's neutral badges. Check versions against `pyproject.toml`; a planned
  release does not change that version. Existing Python badges must agree with
  `requires-python`. Do not fabricate CI status, license, email, or coverage.
  No badge or external link needs a network request for this trial.
- Use top-level `# English` followed by `# 한국어`. README sections match across
  languages in this order: Overview, Features, Prerequisites, Installation,
  Usage, [Configuration], [Project Structure], [Testing], [API Documentation],
  Contributing, License, Contact. Brackets mark optional sections, not literal
  heading text. New files use the guide's exact Korean heading mapping;
  existing custom headings stay in place.
  Include optional sections only when applicable; this CLI has no HTTP API.
  State missing license/contact information honestly. Preserve custom operator
  sections in their existing relative positions.
- Include a Keep a Changelog notice in each language and describe the actual
  or explicitly adopted version policy. Use h2 headings for
  Unreleased and dated releases, newest first. Use the English h3 category names
  Added, Changed, Deprecated, Removed, Fixed, and Security in **both** language
  sections, including only applicable categories.
- Keep shared reference definitions once at each file's end, after Korean
  content. Both languages use the same definitions. References must come from
  local evidence or an explicitly planned release; an example origin does not
  prove remote availability. The baseline `v0.3.0` tag is real locally. The
  `0.2.0` history deliberately has no evidenced tag and is unlinked.

### Inspect sync behavior and repeat it

The README contains obsolete Python requirements, a wrong English command,
old JSON field names, and claims that delimiters/pretty output are unsupported
and blank numeric cells stop processing. Inspect current source, manifest, and
the local diff from `v0.3.0`. In the authoring cases, these local checks are
available; record results only if actually run:

```bash
python3 -B csv_report.py sample.csv --column amount
python3 -B csv_report.py sample-semicolon.csv --column amount --delimiter ';' --pretty
make test
```

Run them from the relevant fixture directory; the semicolon sample belongs to
the new Git-backed cases. Both examples produce rows `2` and total `6.0`; the
semicolon sample includes a blank numeric cell which is not counted. The
updated CLI supports `--delimiter` and `--pretty`, and still requires `--column`.
Never execute project checks during `check-only`.

In the sync changelog, the delimiter addition is already recorded in English
but absent in Korean. Pretty JSON already appears in both. The blank-cell fix
is missing from both. Verify that sync reconciles these facts once per language
in Unreleased, preserves the existing pretty-output entry, and leaves the
released `0.3.0` and `0.2.0` blocks byte-for-byte intact. Check each README's
operator paragraph, the untouched `operator-notes.txt`, section order, and
semantic parity of prose, flags, defaults, and examples.

Set `trial_root` to the printed root. After the first sync, capture:

```bash
trial_root=/tmp/project-init-skill-trials-REPLACE_ME
python3 -B tests/skill_trials.py --snapshot "$trial_root/bilingual-sync" \
  > "$trial_root/bilingual-sync-after-1.json"
```

In another fresh context, reapply the **same printed sync request** to that
same project without changing the code or resetting the documents. Capture:

```bash
python3 -B tests/skill_trials.py --snapshot "$trial_root/bilingual-sync" \
  > "$trial_root/bilingual-sync-after-2.json"
```

The second run should leave the documents unchanged: no extra changelog
bullets, language blocks, badge definitions, or reordered sections. The snapshot
command only reads files and local Git metadata; store its output outside the
fixture. It also works for the original cases. For README-only, repeat the
request; for initialization, follow with a sync request and review any edits.

### Inspect release preparation and metadata

Use the untouched `changelog-release` project from the manifest, independently
of the sync result. Its request supplies `0.4.0` and `2026-09-15`, selects the
delimiter addition and blank-cell fix, and defers pretty JSON. Verify that only
those selected bullets move from Unreleased into the new release in each
language. Pretty JSON must remain under Unreleased even though it shares Added
with the selected delimiter entry. Preserve both older released blocks exactly,
their dates/order, and the shared definitions for existing releases.

The local tag prefix supports planning `v0.4.0`; it does not authorize creating
that tag. If comparison links are prepared, `0.4.0` may use
`compare/v0.3.0...v0.4.0`, and Unreleased may use `compare/v0.4.0...HEAD` under the
declared example repository. Record `v0.4.0` as **planned**, not existing or
published. Do not invent a `v0.2.0` ref, contact the origin, change
`pyproject.toml`, stage files, commit, or mutate refs/config/hooks.

To exercise explicitly planned refs after the first result, send:
`0.4.0은 v0.4.0 태그로 공개할 예정이야. 이 계획에 맞게 CHANGELOG의 버전 비교 링크도 준비해줘.`
Verify the new shared definitions and the publication note while the real
tag set, version file, deferred entry, and older releases remain unchanged.

After release preparation:

```bash
python3 -B tests/skill_trials.py --snapshot "$trial_root/changelog-release" \
  > "$trial_root/changelog-release-after.json"
```

From the source repository, compare snapshots for both cases:

```bash
python3 -B - "$trial_root" <<'PY'
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])

def load(name):
    return json.loads((root / name).read_text(encoding="utf-8"))

def without_caches(files):
    return {name: digest for name, digest in files.items()
            if "__pycache__" not in Path(name).parts
            and not name.endswith((".pyc", ".pyo"))}

for case, allowed, runs in (
    ("bilingual-sync", {"README.md", "CHANGELOG.md"}, ("after-1", "after-2")),
    ("changelog-release", {"CHANGELOG.md"}, ("after",)),
):
    baseline = without_caches(load(case + "-before.json"))
    metadata = load(case + "-metadata-before.json")
    previous = None
    for run in runs:
        result = load(case + "-" + run + ".json")
        current = without_caches(result["files"])
        changed = sorted(name for name in baseline.keys() | current.keys()
                         if baseline.get(name) != current.get(name))
        assert result["metadata"] == metadata, (case, run, "metadata changed")
        assert set(changed) <= allowed, (case, run, changed)
        if previous is not None:
            assert current == previous, (case, run, "repeat changed files")
        print(case, run, "metadata preserved; changed paths:", changed)
        previous = current
PY
```

These comparisons cover refs (including absent/present tags), HEAD, index,
config/remotes, version authority, and unrelated files. They do not prove that
the documentation is correct: review the actual diff and preservation/parity
criteria too. Python cache files are separated from authored changes; inspect
them if unexpected. For read-only checks, compare **all** file hashes without
excluding caches.

### Record results

Record the generated root, exact request, source skill revision, agent/context,
write scope, commands with exit codes/output, reviewed code facts, format and
language parity, preserved custom text/history, and snapshot differences.
Include the first and repeated sync results and the independent release result.
Distinguish fixture generation/metadata verification from an actual agent
authoring trial. Mark unperformed steps, missing Git, or incomplete audit
coverage explicitly; do not infer a pass from successful generation.

These are qualitative regression trials, not a numerical skill score. Do not
put fixed test/file totals into the result template or guidance. Keep evidence
beside the projects and clean up only the generated temporary root after review.

<a id="korean"></a>
## 한국어

Python 테스트는 도우미를 검증합니다. 스킬 변경에는 실제 작성·검토 시나리오도
필요합니다. 메타데이터 검증만으로 요청 범위 보존, 내용의 정확성, 반복 실행
동작을 입증할 수는 없습니다. 스킬 본문에 특정 단어나 제목이 있는지가 아니라
실제 작성 결과를 검토합니다.

### 생성과 격리

Python 3.9 이상과 로컬 Git이 필요합니다. 저장소 루트에서 실행합니다.

```bash
python3 -B tests/skill_trials.py
```

[생성 도구](../../tests/skill_trials.py)는 새로운 임시 프로젝트를 만들고,
경로와 실제 작업처럼 작성한 사용자 요청을 출력합니다. 같은 목록은 프로젝트
옆의 `trials.json`에도 저장합니다. 모델을 호출하거나 프로젝트를 실행하지
않습니다. 각 프로젝트에는 표준 라이브러리 CSV CLI, 예제 데이터, 테스트가
있습니다. `CASE-before.json`에는 로컬 Git 파일을 포함한 파일 해시를,
`CASE-metadata-before.json`에는 버전 파일 해시와 로컬 Git HEAD, refs,
인덱스 해시·항목, 설정 해시, 원격 URL을 기록합니다.

기존 `readme-only`와 `initialize`에는 Git 저장소가 없습니다.
`check-only`는 커밋이 없는 로컬 저장소를 유지합니다. 합성 개인 키 헤더가
인덱스에 스테이징되어 있고, 작업 파일은 일반 텍스트로 교체되어 있습니다.

`bilingual-sync`와 `changelog-release`는 서로 독립된 로컬 저장소이며 생성
직후 작업 트리는 깨끗합니다. 각각 `main` 브랜치, `v0.3.0` 릴리스 태그,
그 이후의 CLI 변경 커밋이 있습니다. `pyproject.toml`의 버전은 `0.3.0`입니다.
생성 과정에는 합성 작성자 정보, 고정된 커밋 날짜, 빈 Git 템플릿, 비활성화된
훅과 서명, 격리된 설정을 사용하며 자격 증명 도우미와 전송 기능을 차단합니다.
등록된 origin `https://github.com/example/csv-report.git`은 오프라인 예시이며,
호스팅된 저장소나 지원 서비스가 존재한다는 근거가 아닙니다. 로컬 커밋과 태그
생성은 시나리오 준비에만 해당하며 문서 작성 작업에 포함되지 않습니다.
원격에 접속하거나 실제 자격 증명을 사용하지 않습니다.

각 출력된 요청은 새 에이전트 문맥에서 소스 스킬
`skills/project-init/SKILL.md`로 수행합니다. 요청과 프로젝트 원본만 전달하고,
이 평가 가이드와 스냅샷은 에이전트 문맥에서 제외합니다. 쓰기 범위는 아래 표로
제한하며 설치, fetch, push, 외부 링크·배지 조회 없이 오프라인으로 실행합니다.
시나리오 명령에는 `GIT_OPTIONAL_LOCKS=0`을 설정해 부수적인 인덱스 갱신을
피합니다. 합성 Git 이메일은 시나리오 메타데이터이며 프로젝트 연락처가
아닙니다. 작업 후 실제 결과 파일과 출력을 검토합니다.

| 시나리오 | 쓰기 범위 | 작업 후 확인할 근거 |
|---|---|---|
| `readme-only` | `README.md` | 올바른 진입점·필수 `--column`·예제 출력, 한국어 운영 메모와 릴리스 이력 보존, 관련 없는 파일 유지 |
| `check-only` | 없음 | 깨진 링크·지원하지 않는 옵션·잘못된 명령·인덱스에만 있는 키 헤더 탐지, 비밀 값 비공개, 모든 파일·인덱스 해시 유지, 프로젝트 테스트 미실행 |
| `initialize` | 필요한 프로젝트 문서 | CLI에 근거한 유용한 영어·한국어 문서, 기존 코드 보존, 서비스·라이선스·릴리스 이력·Git 설정을 만들어 내지 않음 |
| `bilingual-sync` | `README.md`, `CHANGELOG.md` | 양쪽 언어의 오래된 README 정보 수정, 운영자 문구와 릴리스 이력 보존, 중복 없이 Unreleased 번역 보완, 두 번째 동기화 결과 유지 |
| `changelog-release` | `CHANGELOG.md` | 선택한 Unreleased 항목만 지정 버전·날짜로 양쪽 언어에서 이동, 보류 항목과 과거 이력 보존, README·프로젝트 버전·Git 메타데이터 유지 |

### 요청된 기본 형식 검토

새 문서나 명시적인 형식 전환에는
[README](../../skills/project-init/references/readme.md)와
[CHANGELOG](../../skills/project-init/references/changelog.md) 규격을 적용합니다.
기존 한국어 전용·사용자 정의 이중 언어 시나리오는 헤딩·메모·구조를 유지하며,
형식을 강제로 바꾸지 않고 역할과 양 언어의 사실을 비교합니다.

- 새 README는 라이선스·빌드·버전·언어 배지 한 줄을, 새 변경 이력은 언어
  배지를 사용합니다. 이미지 주소는 `img.shields.io`, 언어 링크는
  `#english`·`#한국어`를 사용합니다. 라이선스·빌드 정보가 없으면 지침의
  중립 배지를 사용합니다. 버전은 `pyproject.toml`과 대조하며 릴리스 계획만으로
  바뀌지 않습니다. 기존 Python 배지는 `requires-python`과 일치해야 합니다.
  CI 상태·라이선스·이메일·커버리지를 지어내지 않으며 배지나 외부 링크
  검토를 위한 네트워크 요청도 필요하지 않습니다.
- 최상위 `# English` 다음에 `# 한국어`를 둡니다. README의 대응 섹션 순서는
  Overview, Features, Prerequisites, Installation, Usage, [Configuration],
  [Project Structure], [Testing], [API Documentation], Contributing, License,
  Contact입니다. 대괄호는 선택 사항을 뜻하며 실제 제목에 넣지 않습니다.
  새 문서는 지침의 정확한 한국어 헤딩 대응을 사용하고 기존 사용자 정의
  헤딩은 유지합니다. 선택 섹션은 해당할 때만 포함합니다.
  이 CLI에는 HTTP API가 없습니다. 라이선스나 연락처가 없으면
  그 사실을 명시합니다. 사용자 운영 메모 섹션의 상대적인 위치도 유지합니다.
- 양쪽 언어에 Keep a Changelog 안내와 실제 또는 명시적으로 채택한 버전
  정책을 설명합니다. Unreleased와 날짜가 있는
  릴리스는 h2로, 최신 순서로 배치합니다. h3 범주는 **양쪽 언어 모두** 영어
  이름 Added, Changed, Deprecated, Removed, Fixed, Security를 사용하며,
  해당하는 범주만 포함합니다.
- 공유 참조 정의는 파일마다 한국어 내용 뒤의 맨 끝에 한 번만 둡니다.
  양쪽 언어가 같은 정의를 사용해야 합니다. 참조는 로컬 근거나 명시적으로
  계획한 릴리스에 기반해야 하며, 예시 origin이 원격 접속 가능성을 증명하지는
  않습니다. 기준 태그 `v0.3.0`은 로컬에 실제로 존재합니다. `0.2.0` 이력에는
  근거가 있는 태그를 의도적으로 제공하지 않았으며 링크도 없습니다.

### 동기화 동작과 반복 실행 확인

README에는 오래된 Python 요구 사항, 잘못된 영어 실행 명령, 이전 JSON 필드명,
구분자 선택·들여쓰기 출력 미지원 및 빈 숫자 셀에서 실행이 중단된다는 설명이
있습니다. 현재 코드, 매니페스트, `v0.3.0` 이후 로컬 diff와 대조합니다.
작성 시나리오에서는 다음 로컬 검증을 사용할 수 있으며, 실제 실행한 결과만
기록합니다.

```bash
python3 -B csv_report.py sample.csv --column amount
python3 -B csv_report.py sample-semicolon.csv --column amount --delimiter ';' --pretty
make test
```

해당 시나리오 디렉터리에서 실행합니다. 세미콜론 예제는 새 Git 저장소
시나리오에 있습니다. 두 예제의 결과는 rows `2`, total `6.0`이며,
세미콜론 예제의 빈 숫자 셀은 행 수에 포함하지 않습니다. 현재 CLI는
`--delimiter`와 `--pretty`를 지원하고 `--column`은 여전히 필수입니다.
`check-only`에서는 프로젝트 검증 명령을 실행하지 않습니다.

동기화용 CHANGELOG에는 구분자 선택 항목이 영어에만 있고 한국어에는 없습니다.
JSON 들여쓰기는 양쪽에 이미 있으며, 빈 셀 수정 항목은 양쪽 모두 빠져 있습니다.
동기화 후 Unreleased의 각 언어에 항목이 한 번씩만 있는지, 기존 들여쓰기 항목은
유지됐는지, `0.3.0`과 `0.2.0`의 릴리스 블록이 바이트 단위로 보존됐는지
확인합니다. README의 각 운영 메모 문단, 수정하지 않은 `operator-notes.txt`,
섹션 순서, 설명·옵션·기본값·예제의 의미상 언어 일치 여부도 검토합니다.

`trial_root`를 출력된 루트 경로로 설정하고 첫 동기화 후 스냅샷을 저장합니다.

```bash
trial_root=/tmp/project-init-skill-trials-REPLACE_ME
python3 -B tests/skill_trials.py --snapshot "$trial_root/bilingual-sync" \
  > "$trial_root/bilingual-sync-after-1.json"
```

다른 새 문맥에서 **출력된 동기화 요청을 그대로** 같은 프로젝트에 다시
적용합니다. 코드를 변경하거나 문서를 초기 상태로 되돌리지 않습니다.
두 번째 결과를 저장합니다.

```bash
python3 -B tests/skill_trials.py --snapshot "$trial_root/bilingual-sync" \
  > "$trial_root/bilingual-sync-after-2.json"
```

두 번째 실행에서는 문서가 유지되어야 합니다. CHANGELOG 항목, 언어 블록,
배지 정의가 늘어나거나 섹션 순서가 바뀌면 안 됩니다. 스냅샷 명령은 파일과
로컬 Git 메타데이터를 읽기만 하며, 출력은 시나리오 디렉터리 밖에 저장합니다.
기존 시나리오에도 사용할 수 있습니다. README만 수정한 경우 같은 요청을
반복하고, 초기화한 경우 동기화를 후속 요청해 변경 내용을 검토합니다.

### 릴리스 준비와 메타데이터 확인

동기화 결과와 무관하게 목록의 원본 `changelog-release` 프로젝트를 사용합니다.
요청에는 버전 `0.4.0`, 날짜 `2026-09-15`, 이번에 포함할 구분자 선택과 빈 셀
수정, 보류할 JSON 들여쓰기가 명시되어 있습니다. 양쪽 언어의 Unreleased에서
선택한 항목만 새 릴리스로 이동했는지 확인합니다. JSON 들여쓰기는 구분자
항목과 같은 Added 범주에 있어도 Unreleased에 남아야 합니다. 과거 릴리스
블록과 날짜·순서, 기존 릴리스의 공유 참조 정의를 그대로 보존합니다.

로컬 태그 접두사에 따라 `v0.4.0`을 계획할 수 있지만 생성 권한까지 주어지는
것은 아닙니다. 비교 링크를 준비한다면 등록된 예시 저장소 아래에서
`0.4.0`에는 `compare/v0.3.0...v0.4.0`, Unreleased에는
`compare/v0.4.0...HEAD`를 사용할 수 있습니다. `v0.4.0`은 존재하거나 게시된
태그가 아니라 **계획된 태그**로 기록합니다. `v0.2.0` 참조를 지어내거나,
origin에 접속하거나, `pyproject.toml`을 변경하거나, 스테이징·커밋하거나,
refs·설정·훅을 변경하면 안 됩니다.

첫 결과 이후 명시적인 태그 계획을 검증하려면 다음 요청을 전달합니다.
`0.4.0은 v0.4.0 태그로 공개할 예정이야. 이 계획에 맞게 CHANGELOG의 버전 비교 링크도 준비해줘.`
새 공통 링크 정의와 공개 전 안내를 확인하고 실제 태그 목록·버전 파일·보류
항목·과거 릴리스는 그대로인지 비교합니다.

릴리스 문서 준비 후 스냅샷을 저장합니다.

```bash
python3 -B tests/skill_trials.py --snapshot "$trial_root/changelog-release" \
  > "$trial_root/changelog-release-after.json"
```

소스 저장소에서 두 시나리오의 스냅샷을 비교합니다.

```bash
python3 -B - "$trial_root" <<'PY'
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])

def load(name):
    return json.loads((root / name).read_text(encoding="utf-8"))

def without_caches(files):
    return {name: digest for name, digest in files.items()
            if "__pycache__" not in Path(name).parts
            and not name.endswith((".pyc", ".pyo"))}

for case, allowed, runs in (
    ("bilingual-sync", {"README.md", "CHANGELOG.md"}, ("after-1", "after-2")),
    ("changelog-release", {"CHANGELOG.md"}, ("after",)),
):
    baseline = without_caches(load(case + "-before.json"))
    metadata = load(case + "-metadata-before.json")
    previous = None
    for run in runs:
        result = load(case + "-" + run + ".json")
        current = without_caches(result["files"])
        changed = sorted(name for name in baseline.keys() | current.keys()
                         if baseline.get(name) != current.get(name))
        assert result["metadata"] == metadata, (case, run, "metadata changed")
        assert set(changed) <= allowed, (case, run, changed)
        if previous is not None:
            assert current == previous, (case, run, "repeat changed files")
        print(case, run, "metadata preserved; changed paths:", changed)
        previous = current
PY
```

이 비교에는 태그의 존재 여부를 포함한 refs, HEAD, 인덱스, 설정·원격,
버전의 기준 파일, 관련 없는 파일이 포함됩니다. 문서 내용이 정확하다는 뜻은
아니므로 실제 diff와 보존·언어 일치 기준도 검토합니다. Python 캐시 파일은
작성한 변경과 구분하며 예상하지 못한 캐시는 따로 살펴봅니다. 읽기 전용 점검은
캐시도 제외하지 않고 **모든** 파일 해시를 비교합니다.

### 결과 기록

생성 루트, 실제 요청, 소스 스킬 리비전, 에이전트·문맥, 쓰기 범위, 명령과
종료 코드·출력, 코드에서 확인한 사실, 형식과 언어 일치 여부, 사용자 문구와
과거 이력의 보존 여부, 스냅샷 차이를 기록합니다. 첫 동기화와 반복 동기화,
독립적으로 수행한 릴리스 준비 결과를 포함합니다. 시나리오 생성·메타데이터
검증과 실제 에이전트 작성 시나리오 실행을 구분합니다. 수행하지 않은 단계,
Git 부재, 불완전한 검사 범위는 명시하며 생성 성공만으로 통과를 판단하지
않습니다.

이 시나리오는 정성적인 회귀 검증이며 수치형 스킬 점수가 아닙니다.
기록 양식이나 가이드에 고정된 테스트·파일 개수를 넣지 않습니다. 근거는
프로젝트 옆에 보관하고, 검토 후 생성한 임시 루트만 정리합니다.
