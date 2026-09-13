# Auditor contract

[![English](https://img.shields.io/badge/lang-English-blue)](#english) [![한국어](https://img.shields.io/badge/lang-%ED%95%9C%EA%B5%AD%EC%96%B4-red)](#한국어)

<a id="english"></a>
## English

The stable CLI entrypoint is
[project_audit.py](../../skills/project-init/scripts/project_audit.py). It requires
Python 3.9+ and its sibling `project_init_audit` package, with no third-party
Python dependencies. Git is optional for inspection and required for commit
preflight. The JSON report is written to stdout; invocation errors use stderr.

### Commands

```bash
python3 skills/project-init/scripts/project_audit.py inspect /path/to/project
python3 skills/project-init/scripts/project_audit.py check /path/to/project
python3 skills/project-init/scripts/project_audit.py check /path/to/project \
  --profile existing --require-document guide/start.md
python3 skills/project-init/scripts/project_audit.py check /path/to/project \
  --profile existing --for-commit
```

`inspect` returns observations, with exit code 0. `check` returns 1 for errors
and 0 for warnings/pass. Invalid arguments or a nonexistent target return 2.
`--profile`, `--require-document`, and `--for-commit` apply only to `check`.

| Option | Contract |
|---|---|
| `--profile core` (default) | Require AGENTS, README, changelog, ignore rules, docs index, architecture, and onboarding |
| `--profile existing` | Inspect existing Markdown documents without requiring a full layout |
| `--require-document PATH` | Also require a specific target-relative file; may be repeated |
| `--for-commit` | Require Git and check scoped whitespace, conflicts, and staged indicators |

Core roles accept conventional alternatives, including `README.rst`,
`CHANGES.md`, `HISTORY.md`, `docs/index.md`, `doc/README.md`, `ARCHITECTURE.md`,
and `docs/getting-started.md`. Use explicit requirements with the existing
profile for another layout. Presence establishes structure, not content quality.

### Report

| Field | Meaning |
|---|---|
| `schema_version` | JSON contract version; currently `1` |
| `project` | Metadata, manifests, languages, candidate layers, and command provenance |
| `project.command_evidence` | Source path and `declared` or `conventional` for each suggested command |
| `git.root` / `git.scope` | Enclosing Git root and the target's relative scope |
| `git.dirty` / `git.staged_paths` | State within that scope; staged paths are target-relative |
| `scan.complete` | Whether the requested inventory/content scans avoided omissions or failures |
| `scan.skipped` / `scan.limits` | Unreadable/skipped paths and scan bounds |
| `findings` | Code, path, message, and severity; no matched secret values |
| `checks_run` | Structural checks actually performed; never project test results |
| `status` | `observed`, `pass`, `warn`, or `fail` |

A zero exit code can accompany an incomplete scan. Inspect findings and coverage
before using the result. Missing Git metadata is a warning for ordinary checks
and an error for commit preflight. An empty staged scope is a warning; a missing
remote does not prevent a local commit.

### Boundaries

The inventory uses Git ignore rules in a valid worktree, retaining tracked files.
Common dependency/build/cache directories are omitted. External file symlinks,
symlinked directories, special files, unreadable content, oversized files, and
entry-limit exhaustion are reported. Filesystem reads do not create bytecode
caches or modify the target.

Markdown inline/reference links and HTML `href`/`src` file targets are checked.
Fenced and inline code, comments, and escaped examples are ignored. File targets
beginning with `/` are relative to the selected project. Heading anchors,
external websites, site-generator routes, and full CommonMark rendering are not
validated. RST/plain core documents are checked for presence and content, not
RST links.

Document checks describe the working tree. Commit preflight separately reads
index blobs and checks scoped diffs. Git hooks, fsmonitor, clean/process filters,
external diffs, text conversion, and network protocols are disabled for these
observations. Inherited Git environment overrides and global Git configuration
do not redirect the audit. Git reads local repository metadata, including an
enclosing repository or linked worktree; the file inventory stays within the
selected target. Git metadata is checked for filesystem symlinks before Git is
invoked. Metadata symlinks, local Git configuration includes, or metadata
inventory limits make Git observations unavailable and coverage incomplete.
The auditor does not expand the Git include language or global ignore/attribute
files. A normal Git worktree pointer file remains supported.

Secret indicators cover private-key headers, AWS access-key IDs, GitHub token
shapes, and selected credential filenames. Binary/large blobs and submodule
contents remain unverified. This is a limited preflight, not a comprehensive
secret scanner or proof that a commit is safe to publish.

Python/Rust TOML metadata extraction handles single-line literal strings.
Dynamic versions, inherited workspace metadata, complex TOML, architecture
claims, translations, and command correctness require source review. See
[check and review](../../skills/project-init/references/check.md).

<a id="korean"></a>
## 한국어

CLI 진입점은 [project_audit.py](../../skills/project-init/scripts/project_audit.py)입니다.
Python 3.9 이상과 같은 디렉터리의 `project_init_audit` 패키지가 필요하며 외부
Python 의존성은 없습니다. 일반 조사에서 Git은 선택 사항이고 커밋 사전 검사에는
필수입니다. JSON 결과는 stdout, 잘못된 호출에 대한 오류는 stderr로 출력합니다.

### 명령

```bash
python3 skills/project-init/scripts/project_audit.py inspect /path/to/project
python3 skills/project-init/scripts/project_audit.py check /path/to/project
python3 skills/project-init/scripts/project_audit.py check /path/to/project \
  --profile existing --require-document guide/start.md
python3 skills/project-init/scripts/project_audit.py check /path/to/project \
  --profile existing --for-commit
```

`inspect`는 관찰 결과와 종료 코드 0을 반환합니다. `check`는 오류가 있으면 1,
경고만 있거나 통과하면 0을 반환합니다. 잘못된 인수나 존재하지 않는 대상은 2를
반환합니다. `--profile`, `--require-document`, `--for-commit`은 `check`에서만
사용할 수 있습니다.

| 옵션 | 동작 |
|---|---|
| `--profile core` (기본값) | AGENTS·README·변경 이력·ignore 규칙·문서 목차·아키텍처·온보딩 요구 |
| `--profile existing` | 전체 문서 구조를 요구하지 않고 기존 Markdown 문서 검사 |
| `--require-document PATH` | 대상 기준 상대 경로의 파일을 추가로 요구하며 반복 지정 가능 |
| `--for-commit` | Git을 요구하고 지정 범위의 공백·충돌·스테이징 징후 검사 |

핵심 역할은 `README.rst`, `CHANGES.md`, `HISTORY.md`, `docs/index.md`,
`doc/README.md`, `ARCHITECTURE.md`, `docs/getting-started.md` 같은 일반적인
대체 경로도 인정합니다. 다른 구조에서는 existing 프로필에 필수 경로를
명시합니다. 파일의 존재는 구조에 대한 근거이며 내용의 품질을 보증하지 않습니다.

### 결과

| 필드 | 의미 |
|---|---|
| `schema_version` | JSON 계약 버전이며 현재 `1` |
| `project` | 메타데이터·매니페스트·언어·구현 계층 후보·명령 출처 |
| `project.command_evidence` | 명령별 출처 경로와 `declared` 또는 `conventional` 구분 |
| `git.root` / `git.scope` | 상위 Git 루트와 대상의 상대 범위 |
| `git.dirty` / `git.staged_paths` | 지정 범위의 상태이며 스테이징 경로는 대상 기준 상대 경로 |
| `scan.complete` | 요청한 파일 탐색과 내용 검사에서 누락·실패가 없었는지 여부 |
| `scan.skipped` / `scan.limits` | 읽지 못했거나 건너뛴 경로와 검사 한도 |
| `findings` | 코드·경로·메시지·심각도이며 일치한 비밀 값은 제외 |
| `checks_run` | 실제 수행한 구조 검사이며 프로젝트 테스트 결과가 아님 |
| `status` | `observed`, `pass`, `warn`, `fail` 중 하나 |

종료 코드가 0이어도 검사가 불완전할 수 있습니다. 결과를 활용하기 전에 발견
사항과 검사 범위를 확인하세요. Git 메타데이터 부재는 일반 검사에서는 경고,
커밋 사전 검사에서는 오류입니다. 지정 범위에 스테이징된 변경이 없으면 경고이며,
원격 저장소가 없어도 로컬 커밋은 가능합니다.

### 범위와 한계

유효한 Git 작업 트리에서는 ignore 규칙을 적용하며 추적 중인 파일은 유지합니다.
일반적인 의존성·빌드·캐시 디렉터리는 제외합니다. 외부 파일 심볼릭 링크, 심볼릭
링크 디렉터리, 특수 파일, 읽기 실패, 큰 파일, 탐색 한도 도달을 결과에 표시합니다.
파일을 읽으면서 바이트코드 캐시를 만들거나 대상을 수정하지 않습니다.

Markdown 인라인·참조 링크와 HTML `href`/`src`의 파일 대상을 검사합니다.
코드 블록·인라인 코드·주석·이스케이프된 예시는 제외합니다. `/`로 시작하는
파일 대상은 선택한 프로젝트 기준입니다. 제목 앵커, 외부 웹사이트, 사이트 생성기
라우트, 전체 CommonMark 렌더링은 검증하지 않습니다. RST·일반 텍스트 핵심 문서는
존재와 내용 유무를 확인하지만 RST 링크는 검사하지 않습니다.

문서 검사는 작업 트리를 기준으로 합니다. 커밋 사전 검사에서는 인덱스 blob과
지정 범위의 diff를 별도로 읽습니다. Git 훅·fsmonitor·clean/process 필터·외부
diff·텍스트 변환·네트워크 프로토콜을 비활성화합니다. 상속된 Git 환경 변수나
전역 Git 설정이 검사 대상을 바꾸지 않습니다. Git은 상위 저장소나 연결된
worktree를 포함한 로컬 메타데이터를 읽고, 파일 탐색은 선택한 대상 안에 머뭅니다.
Git 호출 전에 메타데이터의 파일 심볼릭 링크를 확인합니다. 메타데이터 심볼릭
링크, 로컬 Git 설정의 include, 메타데이터 탐색 한도에 걸리면 Git 조사를
중단하고 검사 범위가 불완전함을 표시합니다. Git include 문법이나 전역
ignore·attribute 파일을 확장하지 않습니다. 정상적인 Git worktree 포인터
파일은 계속 지원합니다.

시크릿 징후는 개인 키 헤더, AWS 액세스 키 ID, GitHub 토큰 형태, 일부 자격 증명
파일 이름을 확인합니다. 바이너리·큰 blob·서브모듈 내용은 검증되지 않습니다.
제한된 사전 검사이며 완전한 시크릿 스캐너나 공개 가능한 커밋의 보증이 아닙니다.

Python·Rust TOML 메타데이터는 한 줄 문자열 리터럴을 읽습니다. 동적 버전,
워크스페이스 상속, 복잡한 TOML, 아키텍처 설명, 번역, 명령의 정확성은 소스를
검토해야 합니다. [점검과 검토](../../skills/project-init/references/check.md)를
참고하세요.
