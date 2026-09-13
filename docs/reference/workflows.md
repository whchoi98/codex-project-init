# Workflow Reference

[![English](https://img.shields.io/badge/lang-English-blue)](#english) [![한국어](https://img.shields.io/badge/lang-%ED%95%9C%EA%B5%AD%EC%96%B4-red)](#한국어)

<a id="english"></a>
## English

### Overview
`project-init` is an instruction-driven workflow; the auditor is a separate CLI.

### Components
The skill uses focused references and templates only for the requested operation.
Initialization fills relevant gaps; synchronization updates affected documents;
targeted additions stay within the requested scope. `check` inspects and reports
without writing documents or running project tests. Authoring and commit
preparation select missing required checks and reuse valid evidence.

### Verification ownership

Project Init owns document accuracy and scoped document/index checks. The primary
development/test workflow and existing reviewer own implementation verification.
Ordinary commit/push requests do not select this skill; explicit `prepare-commit`
keeps document preparation available without creating another test/review pipeline.

The [verification policy](../../skills/project-init/references/verification.md)
defines change-based scope, input matching, invalidation, and result reporting.
A current `check` already includes project observations, so read-only review
does not need another `inspect`. Full-suite and release requirements remain
applicable when explicitly required.

### README and CHANGELOG

Initialization, targeted authoring, and `sync` / `sync-doc` / `sync-docs` use
the same dedicated writing guides. New README/changelog files use Shields
language badges, `# English` and `# 한국어` blocks, and matching content/order.
The README guide defines required and conditional sections. The changelog guide
uses Keep a Changelog categories, Unreleased, preserved releases, and shared
reference links backed by actual or explicitly planned refs.

All bilingual public documents use the same Shields language navigation,
including indexes, architecture, onboarding, contribution guidance, ADRs,
runbooks, and implementation references. Preserve their heading levels and
legacy anchors when replacing earlier text navigation.

Sync maps source changes to existing sections, reconciles both languages, and
deduplicates Unreleased entries by meaning. It preserves custom notes, existing
single-language layouts, and published history. Format adoption is explicit.
Unknown CI/license/contact/tag information stays truthful; it is not filled
with sample metadata. These authoring rules are reviewed through behavior
trials; the auditor does not impose the templates on every target.

### Key decisions
Preserve existing conventions and released history. Treat Git mutations as
separate requested actions; see the [ADR](../decisions/ADR-001-codex-native-workflows.md).
Repeated synchronization with no new evidence should leave documents unchanged.

### Code pointers

- [Skill entrypoint](../../skills/project-init/SKILL.md)
- [Document conventions](../../skills/project-init/references/documents.md)
- [README guide](../../skills/project-init/references/readme.md) and
  [template](../../skills/project-init/assets/readme.md)
- [CHANGELOG guide](../../skills/project-init/references/changelog.md) and
  [template](../../skills/project-init/assets/changelog.md)
- [Auditor](../../skills/project-init/scripts/project_audit.py)
### Cross-references

- [Claude capability mapping](../../skills/project-init/references/migration.md)
- [Git preparation](../../skills/project-init/references/git-preparation.md)
- [Evidence review](../../skills/project-init/references/check.md)
- [Auditor contract](auditor.md)
- [Behavior trials](skill-evaluation.md)
- [Official skill authoring](https://learn.chatgpt.com/docs/build-skills)
- [Official plugin authoring](https://learn.chatgpt.com/docs/build-plugins)

<a id="korean"></a>
## 한국어

### 개요
`project-init`은 지침 기반 작업이며, 검사 도구는 별도 CLI입니다.

### 구성 요소
요청한 작업에 필요한 작성 지침과 템플릿을 선택해 사용합니다.
초기화는 필요한 문서를 채우고, 동기화는 변경에 영향받는 문서를 갱신하며, 개별
추가는 요청 범위를 유지합니다. `check`는 문서를 쓰거나 프로젝트 테스트를
실행하지 않고 조사 결과를 보고합니다. 문서 작성과 커밋 준비에서는 관련 검증을
선택하고 유효한 기존 근거를 재사용합니다.

### 검증 역할 분담

Project Init은 문서의 정확성과 지정 범위의 문서·인덱스 검사를 맡습니다.
구현 검증은 주 개발·테스트 작업과 기존 리뷰어가 담당합니다. 일반 커밋·푸시
요청만으로는 이 스킬을 선택하지 않으며, 명시적인 `prepare-commit`에서는
테스트·리뷰 절차를 새로 만들지 않고 문서 준비를 수행합니다.

[검증 정책](../../skills/project-init/references/verification.md)에 변경별 범위,
입력 비교, 무효화, 결과 보고를 정의합니다. 현재 상태의 `check`에는 프로젝트
관찰 정보가 있으므로 읽기 전용 점검에 별도 `inspect`가 필요하지 않습니다.
명시적으로 요구한 전체 테스트와 릴리스 규칙은 계속 적용합니다.

### README와 CHANGELOG

초기화, 개별 문서 작성, `sync` / `sync-doc` / `sync-docs`는 같은 전용 작성
지침을 사용합니다. 새 README·변경 이력은 Shields 언어 배지, `# English`와
`# 한국어` 블록, 양쪽의 같은 내용·순서를 사용합니다. README 지침은 필수·
조건부 섹션을 정의하고, 변경 이력 지침은 Keep a Changelog 카테고리,
Unreleased, 과거 릴리스 보존, 실제 또는 명시적으로 계획된 ref의 공통
참조 링크를 사용합니다.

문서 목차·아키텍처·온보딩·기여 안내·ADR·런북·구현 참조를 포함한 모든
이중 언어 공개 문서는 같은 Shields 언어 전환 배지를 사용합니다. 기존
텍스트 링크를 교체할 때 헤딩 수준과 이전 앵커를 보존합니다.

동기화는 소스 변경을 기존 섹션에 대응시키고 양 언어를 함께 갱신하며,
Unreleased 항목을 의미 기준으로 중복 제거합니다. 사용자 메모, 기존 단일
언어 구조, 공개된 이력을 유지하며 형식 전환은 명시적인 요청에 따릅니다.
CI·라이선스·연락처·태그 정보가 없으면 예시로 채우지 않고 실제 상태를
설명합니다. 작성 규칙은 동작 시나리오로 검증하며 검사 도구가 모든 대상에
이 템플릿을 강제하지는 않습니다.

### 주요 결정
기존 규칙과 릴리스 이력을 보존합니다. Git 변경은 별도로 요청받은 작업으로
처리합니다. [ADR](../decisions/ADR-001-codex-native-workflows.md)을 참고하세요.
새 근거 없이 동기화를 반복하면 문서 내용을 그대로 유지합니다.

### 코드 위치

- [스킬 진입점](../../skills/project-init/SKILL.md)
- [문서 규칙](../../skills/project-init/references/documents.md)
- [README 지침](../../skills/project-init/references/readme.md)과
  [템플릿](../../skills/project-init/assets/readme.md)
- [CHANGELOG 지침](../../skills/project-init/references/changelog.md)과
  [템플릿](../../skills/project-init/assets/changelog.md)
- [검사 도구](../../skills/project-init/scripts/project_audit.py)
### 관련 문서

- [Claude 기능 대응](../../skills/project-init/references/migration.md)
- [Git 준비](../../skills/project-init/references/git-preparation.md)
- [근거 검토](../../skills/project-init/references/check.md)
- [검사 도구 계약](auditor.md)
- [동작 시나리오](skill-evaluation.md)
- [공식 스킬 작성 지침](https://learn.chatgpt.com/docs/build-skills)
- [공식 플러그인 작성 지침](https://learn.chatgpt.com/docs/build-plugins)
