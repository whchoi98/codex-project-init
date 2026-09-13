# Project Init restructuring plan

[![English](https://img.shields.io/badge/lang-English-blue)](#english) [![한국어](https://img.shields.io/badge/lang-%ED%95%9C%EA%B5%AD%EC%96%B4-red)](#한국어)

<a id="english"></a>
## English

**Goal:** Make Project Init a focused, portable Codex plugin that turns an actual
project into useful documentation and supplies trustworthy, read-only evidence
for review.

**Design:** Keep one discoverable skill, load authoring guidance by operation,
and separate the auditor's filesystem, document, project, and Git responsibilities.
Keep the existing CLI entrypoint and JSON fields. Distribute the same complete
skill in a plugin ZIP and a standalone ZIP.

The maintained Claude project establishes the original intent: mature working
projects through documentation and maintenance workflows. Its runtime hooks,
configuration, generated generic agents, and numerical quality scores are not
requirements of the Codex implementation. The existing ADR remains applicable.

### Requirements and evidence

| Requirement | Completion evidence |
|---|---|
| Discoverable, narrowly routed skill | Metadata validation and independent task trials |
| Preserve user content, scope, languages, and release history | Trials with custom README content, existing history, and a requested subset |
| Read-only, bounded auditor; no project script execution or external file traversal | Temporary filesystem and real Git regression tests; target snapshots |
| Useful findings for real layouts and partial scans | Alternate layouts, explicit document requirements, malformed/unreadable input tests |
| Commit checks read the index and respect the requested subproject | Staged/unstaged, subdirectory, filter/hook, and Git environment tests |
| Python 3.9+, standard library runtime | Compatible syntax and execution on the available Python runtimes |
| Safe local installation with a truthful preview and recovery | Temporary destinations, real helper contracts, and controlled CLI failures |
| Self-contained, reproducible distributions | Repeated-build hashes, extraction, CLI smoke tests, and archive validation |
| Maintained English/Korean public docs | Updated usage, architecture, operating references, Unreleased, and local links |
| Final deliverable matches final source | `make test`, `make check`, `make package`, then archive/content verification |

### Implementation

- [x] Refine skill routing and authoring guidance. Separate a read-only `check`
  from mutating preparation. Honor targeted requests and report semantic evidence.
- [x] Add failing auditor regressions, then separate responsibilities and fix the
  failures. Preserve `inspect` / `check` and add an existing-document profile plus
  explicit required paths for custom layouts.
- [x] Validate and package explicit distribution contents. Use stable metadata
  for repeatable ZIPs and verify both payloads before reporting success.
- [x] Make installation planning, prerequisite checks, source replacement, and
  rollback independently testable without modifying a real user installation.
- [x] Exercise the skill on isolated realistic projects and review resulting
  files against the requests.
- [x] Update public documentation and Unreleased, run release checks, and rebuild
  distributions after the last source or documentation edit.

Source changes are authorized by the restructuring request. This work does not
require a commit, push, hook installation, or changes to the user's live plugin
installation. The current source export has no valid Git metadata.

### Verification record

The complete test suite passed on Python 3.9 and 3.12, including the optional
installed-tool trials in scratch profiles. `make check`, the bundled Codex
skill/plugin validators, and `make package` passed. The only repository finding
was missing Git metadata; released changelog entries remained byte-for-byte
equivalent.

Independent trials confirmed README-only scope, Korean operator-note and history
preservation, read-only file/index snapshots, and stable repeated authoring/sync.
Independent review reproductions for executable Git filters and linked Git
configuration were fixed and rerun. Packaging regressions cover credential
filenames, missing imported submodules, inline command references, and version
changes. The final delivery rebuilds the archives after this record is updated.

<a id="korean"></a>
## 한국어

**목표:** 실제 프로젝트를 유용한 문서로 정리하고, 검토에 신뢰할 수 있는 읽기
전용 근거를 제공하는 집중도 높은 휴대 가능한 Codex 플러그인으로 개선합니다.

**설계:** 검색되는 스킬은 하나로 유지하고 작업별 작성 지침을 필요할 때 읽습니다.
검사 도구는 파일 탐색, 문서, 프로젝트 정보, Git 책임을 분리합니다. 기존 CLI
진입점과 JSON 필드를 유지하며 동일한 완전한 스킬을 플러그인 ZIP과 단독 스킬
ZIP으로 배포합니다.

유지보수 중인 Claude 원본의 핵심 의도는 구현된 프로젝트에 문서와 유지보수
작업 흐름을 갖추는 것입니다. Claude 런타임의 훅, 설정, 범용 에이전트 생성,
수치형 품질 점수는 Codex 구현의 필수 조건이 아닙니다. 기존 ADR을 유지합니다.

### 요구 사항과 검증 근거

| 요구 사항 | 완료 근거 |
|---|---|
| 명확한 검색 조건과 작업 분기 | 메타데이터 검증과 독립적인 실제 작업 시나리오 |
| 사용자 내용·범위·언어·릴리스 이력 보존 | 사용자 README, 기존 이력, 일부 문서만 요청한 시나리오 |
| 읽기 전용 검사와 탐색 한도, 프로젝트 명령 실행·외부 파일 탐색 금지 | 임시 파일·실제 Git 회귀 테스트와 대상 스냅샷 |
| 실제 문서 구조와 부분 검사에 유용한 결과 | 대체 경로, 필수 문서 지정, 손상되거나 읽을 수 없는 입력 테스트 |
| 인덱스 기준 커밋 검사와 하위 프로젝트 범위 유지 | 스테이징·작업 파일 차이, 하위 경로, 필터·훅, Git 환경 테스트 |
| Python 3.9 이상, 표준 라이브러리 런타임 | 호환 문법 검사와 사용 가능한 Python 버전에서 실행 |
| 정확한 미리보기와 복구가 가능한 로컬 설치 | 임시 설치 경로, 실제 도우미 계약, 통제된 CLI 실패 테스트 |
| 독립 실행 가능한 재현성 있는 배포 파일 | 반복 빌드 해시, 압축 해제 후 CLI 실행, 패키지 검증 |
| 영어·한국어 공개 문서 유지 | 사용법·아키텍처·운영 지침·Unreleased·로컬 링크 갱신 |
| 최종 소스와 배포 결과 일치 | `make test`, `make check`, `make package`와 최종 압축 내용 확인 |

### 구현

위 영어 작업 목록에 따라 스킬 지침, 검사 도구, 패키징, 설치, 실제 작업
시나리오 검증을 완료했습니다. 양언어 공개 문서와 Unreleased를 갱신했으며,
최종 편집 이후 배포 파일을 다시 생성합니다.

재구성 요청에 따라 소스를 수정합니다. 이 작업에는 커밋·푸시·훅 설치나 사용자의
실제 플러그인 설치 변경이 필요하지 않습니다. 현재 소스 사본에는 유효한 Git
메타데이터가 없습니다.

### 검증 기록

임시 프로필에서 설치된 도구를 사용하는 선택적 통합 검증을 포함해 Python
3.9와 3.12의 전체 테스트가 통과했습니다. `make check`, Codex 번들 스킬·
플러그인 검증기, `make package`도 통과했습니다. 저장소 검사에는 Git
메타데이터 부재만 남았고, 기존 릴리스 이력의 내용은 그대로 보존됐습니다.

독립 시나리오로 README만 수정하는 범위, 한국어 운영 메모·이력 보존, 읽기 전용
파일·인덱스 스냅샷, 반복 작성·동기화의 안정성을 확인했습니다. 독립 검토에서
재현한 Git 필터 실행과 링크된 Git 설정 문제를 수정하고 다시 확인했습니다.
패키징 회귀 검증은 자격 증명 파일 이름, 빠진 하위 모듈, 인라인 명령 참조,
버전 변경을 포함합니다. 최종 전달 파일은 이 기록을 갱신한 뒤 다시 빌드합니다.
