# Verification scope and result reuse

[![English](https://img.shields.io/badge/lang-English-blue)](#english) [![한국어](https://img.shields.io/badge/lang-%ED%95%9C%EA%B5%AD%EC%96%B4-red)](#한국어)

## English

Project Init verifies documentation and its relationship to the project.
Select checks from the requested change and existing evidence, not from the
presence of a commit/push command. Explicit user requirements and applicable
project rules still determine required checks; do not weaken a mandatory gate.

### Select the smallest sufficient check

| Work in scope | Default verification |
|---|---|
| Ordinary prose, badges, links, or document layout | Review affected content and links; use the appropriate documentation audit; no application test suite |
| Executable documentation, skill instructions/templates, generated-code inputs | Check the affected behavior or generator; select relevant scenarios instead of every scenario |
| Application code, dependencies, tests, or build/test configuration | Reuse applicable implementation-test evidence; the primary development/CI workflow runs missing affected checks |
| Explicit documentation preparation for a commit | Affected document review plus one final audit with `--for-commit`; reuse implementation tests/reviews when valid |
| Push with no changed test inputs | Check Git destination/status as needed; no new documentation or implementation-test pipeline |
| Release or explicitly required broad regression | Perform the required full checks and packaging, once per applicable input state |

A `.md` extension alone does not prove that a file is ordinary prose: prompts,
skill instructions, executable examples, and build inputs can change behavior.
Likewise, the existence of a full-suite command does not make it necessary for
every edit. When the affected check cannot be selected confidently, state the
gap or why broader coverage is required.

### Reuse evidence without hiding gaps

Use actual command results from the conversation, a trusted CI job, or an
existing review workflow. Record a compact execution ledger in the current
context: check/review, owner, target/scope, checked inputs/revision, command and
result, and whether the evidence is reused or newly executed. Do not create a
new project cache or receipt file just to use this skill.

Evidence is reusable when:

- Its origin and outcome are available; a declared command or an unsupported
  “tests passed” note is not proof of execution.
- It covers the relevant source, tests, dependencies/lockfiles, configuration,
  generated inputs, and material runtime/environment requirements.
- Those inputs still match the current work, including relevant staged and
  unstaged changes. Compare available tree/blob IDs, input hashes, or recorded
  diffs rather than assuming that an unchanged HEAD means unchanged files.
- No unresolved failure, required fresh check, or applicable release rule
  invalidates it.

An exact current revision is strong evidence for a clean tree. If only docs,
commit messages, or Git metadata changed, an implementation test can still be
reused after verifying that its own inputs did not change. Results from another
branch, older inputs, or a materially different environment are not equivalent.
Elapsed time alone neither proves nor invalidates a result.

After an input change, rerun only the affected checks whose evidence is stale.
After a failed check, address or report the failure; do not keep retrying without
a changed input or another concrete reason. Report user-provided or externally
verified results as such, never as commands you executed yourself.

### Keep one owner and one report per state

Keep implementation tests with the primary developer/test runner and code review
with the existing reviewer or CI workflow. Project Init consumes their results
and checks document accuracy. If work is delegated, assign disjoint scope and
state who executes each check; other agents review the returned evidence.
Do not launch another full reviewer, test runner, or agent trial for the same
covered work merely to finish documentation or a Git operation.

For read-only review, call `check` directly. For authoring, inspect what is needed,
then audit after actual edits. A `check` report already includes project and Git
observations; do not precede it with an identical `inspect` or run both core and
existing profiles on the same state. When staging is authorized, combine final
document and index verification in one `check ... --for-commit` invocation.
Changes to documents or the index invalidate the corresponding audit evidence,
not every implementation test.

Finish with short, distinct statements for **executed**, **reused**, and
**not needed / unverified**. A reused pass is not a new execution, and a skipped
irrelevant check is not a failed check.

## 한국어

Project Init은 문서와 실제 프로젝트의 일치 여부를 검증합니다.
커밋·푸시 명령의 존재가 아니라 요청한 변경과 기존 근거를 기준으로 검사를
선택합니다. 사용자의 명시적 요구와 프로젝트의 필수 규칙은 계속 따르며,
반드시 수행해야 하는 검사를 임의로 생략하지 않습니다.

### 필요한 최소 검사 선택

| 작업 범위 | 기본 검증 |
|---|---|
| 일반 문장·배지·링크·문서 배치 | 영향받은 내용·링크와 문서 검사; 애플리케이션 전체 테스트는 실행하지 않음 |
| 실행되는 문서·스킬 지침/템플릿·코드 생성 입력 | 관련 동작·생성기와 영향받은 시나리오만 확인 |
| 애플리케이션 코드·의존성·테스트·빌드/검증 설정 | 유효한 테스트 근거 재사용; 주 개발·CI 작업에서 빠진 관련 검사 실행 |
| 명시적인 문서 커밋 준비 | 영향 문서 검토와 마지막 `--for-commit` 검사; 유효한 코드 테스트·리뷰 재사용 |
| 테스트 입력 변경 없는 푸시 | 필요한 Git 대상·상태 확인; 문서·코드 검증 절차를 새로 시작하지 않음 |
| 릴리스·명시적인 전체 회귀 검증 | 해당 입력 상태에 필요한 전체 검사·패키징을 수행 |

`.md` 파일도 프롬프트·스킬 지침·실행 예제·빌드 입력이면 동작에 영향을 줄 수
있습니다. 반대로 전체 테스트 명령이 있다는 이유만으로 매번 실행하지 않습니다.
관련 검사를 확실하게 고를 수 없다면 검증 공백이나 더 넓은 검사가 필요한
이유를 설명합니다.

### 검증 공백 없이 근거 재사용

현재 대화의 실제 명령 결과, 신뢰할 수 있는 CI 작업, 기존 리뷰 결과를 사용합니다.
검사·리뷰 이름, 담당자, 대상·범위, 검증한 입력·리비전, 명령·결과, 재사용 여부를
현재 문맥에 간단히 기록합니다. 스킬 사용만을 위해 프로젝트에 새 캐시나 검증
기록 파일을 만들지 않습니다.

다음 조건을 충족하면 재사용합니다.

- 결과의 출처와 실행 결과가 확인됩니다. 명령 선언이나 근거 없는 “테스트
  통과” 문구만으로 실행했다고 판단하지 않습니다.
- 관련 소스·테스트·의존성/잠금 파일·설정·생성 입력과 중요한 실행 환경을 다룹니다.
- 관련 스테이징·작업 파일 변경을 포함해 현재 입력과 일치합니다. 트리·blob ID,
  입력 해시, 기록된 diff를 비교하며 HEAD가 같다는 이유만으로 일치한다고
  판단하지 않습니다.
- 미해결 실패, 최신 실행 요구, 릴리스 필수 규칙 등으로 무효화되지 않았습니다.

깨끗한 작업 트리의 정확한 현재 리비전은 강한 근거입니다. 문서·커밋 메시지·
Git 메타데이터만 바뀌었다면 테스트 자체의 입력이 같은지 확인하고 구현 테스트를
재사용할 수 있습니다. 다른 브랜치·이전 입력·중요하게 다른 환경의 결과는
동일하지 않습니다. 시간이 지났다는 사실만으로 유효하거나 무효하다고 판단하지
않습니다.

입력이 달라졌다면 해당 변경 때문에 오래된 결과가 된 검사만 다시 실행합니다.
실패하면 수정하거나 실패를 보고하며, 입력 변화나 구체적인 이유 없이 반복하지
않습니다. 사용자 제공·외부 검증 결과는 출처를 밝히고 직접 실행한 결과처럼
표현하지 않습니다.

### 검사 담당자와 상태별 결과 통합

구현 테스트는 주 개발·테스트 담당자, 코드 리뷰는 기존 리뷰어·CI 작업이 맡습니다.
Project Init은 그 결과를 받아 문서의 정확성을 확인합니다. 작업을 나눌 때는
범위와 검사 실행자를 정하고 다른 에이전트는 전달받은 근거를 검토합니다.
문서 작업이나 Git 작업을 끝낸다는 이유만으로 같은 범위의 전체 리뷰·테스트·
에이전트 시나리오를 다시 시작하지 않습니다.

읽기 전용 점검은 `check`를 바로 실행합니다. 문서 작성은 필요한 초기 조사 후
실제 수정이 끝났을 때 검사합니다. `check` 결과에는 프로젝트·Git 관찰 정보가
이미 있으므로 같은 상태의 `inspect`나 core/existing 두 프로필을 중복 실행하지
않습니다. 스테이징이 허용됐다면 마지막 문서·인덱스 검사를
`check ... --for-commit` 한 번으로 합칩니다. 문서나 인덱스가 바뀌면 해당 검사
근거를 갱신하며, 모든 구현 테스트를 무효화하지 않습니다.

최종 보고는 **직접 실행**, **재사용**, **불필요·미검증**을 짧게 구분합니다.
재사용한 통과 결과를 새 실행으로 표시하거나 필요 없는 검사의 생략을 실패로
표시하지 않습니다.
