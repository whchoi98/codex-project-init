# Workflow Reference

<a href="#english">English</a> · <a href="#korean">한국어</a>

<a id="english"></a>
## English

### Overview
`project-init` is an instruction-driven workflow; the auditor is a separate CLI.

### Components
The skill uses focused references and templates only for the requested operation.
Initialization fills relevant gaps; synchronization updates affected documents;
targeted additions stay within the requested scope. `check` inspects and reports
without writing documents or running project tests. Authoring and commit
preparation can execute relevant checks.

### Key decisions
Preserve existing conventions and released history. Treat Git mutations as
separate requested actions; see the [ADR](../decisions/ADR-001-codex-native-workflows.md).
Repeated synchronization with no new evidence should leave documents unchanged.

### Code pointers

- [Skill entrypoint](../../skills/project-init/SKILL.md)
- [Document conventions](../../skills/project-init/references/documents.md)
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
실행할 수 있습니다.

### 주요 결정
기존 규칙과 릴리스 이력을 보존합니다. Git 변경은 별도로 요청받은 작업으로
처리합니다. [ADR](../decisions/ADR-001-codex-native-workflows.md)을 참고하세요.
새 근거 없이 동기화를 반복하면 문서 내용을 그대로 유지합니다.

### 코드 위치

- [스킬 진입점](../../skills/project-init/SKILL.md)
- [문서 규칙](../../skills/project-init/references/documents.md)
- [검사 도구](../../skills/project-init/scripts/project_audit.py)
### 관련 문서

- [Claude 기능 대응](../../skills/project-init/references/migration.md)
- [Git 준비](../../skills/project-init/references/git-preparation.md)
- [근거 검토](../../skills/project-init/references/check.md)
- [검사 도구 계약](auditor.md)
- [동작 시나리오](skill-evaluation.md)
- [공식 스킬 작성 지침](https://learn.chatgpt.com/docs/build-skills)
- [공식 플러그인 작성 지침](https://learn.chatgpt.com/docs/build-plugins)
