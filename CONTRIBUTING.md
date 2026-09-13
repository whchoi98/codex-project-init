# Contributing

[![English](https://img.shields.io/badge/lang-English-blue)](#english) [![한국어](https://img.shields.io/badge/lang-%ED%95%9C%EA%B5%AD%EC%96%B4-red)](#한국어)

<a id="english"></a>
## English

Read [AGENTS.md](AGENTS.md). Preserve custom documentation and historical releases.
Test filesystem and Git behavior with temporary repositories, not live credentials
or remotes. Update both public language sections and the changelog. Select
verification by the affected inputs:

| Change | Required scope |
|---|---|
| Ordinary prose, links, badges | Affected document/link checks; no full application suite |
| Skill instructions or templates | Document checks and the affected behavior trials |
| Python, installation, audit, or packaging behavior | Relevant helper tests; broaden when shared behavior or project rules require it |
| Release | `make test`, `make check`, and `make package` |

Reuse valid results for unchanged inputs and record their source. Keep one
runner/reviewer for each scope. Rebuild distribution archives after the final
source/document edit; reuse that build if its inputs stay unchanged.
Do not edit generated ZIPs. See [verification scope and reuse](skills/project-init/references/verification.md).

Auditor tests exercise real temporary Git repositories and filesystem boundaries.
Installation tests use temporary homes and controlled CLI behavior. Packaging
tests extract both artifacts and check their content. For skill instruction
changes, select affected [behavior trials](docs/reference/skill-evaluation.md) and inspect
actual outputs, preservation, and repeated-run behavior.

When installation/CLI integration changed or a release requires it, enable the
optional installed-tool trials with Codex and its plugin-creator helpers:

```bash
PROJECT_INIT_REAL_INTEGRATION=1 make test
```

These trials use scratch profiles and bundled helpers, including native plugin
installation and refresh from an extracted local catalogue. They do not use
real credentials or the active user profile. `PROJECT_INIT_REAL_CODEX` and
`PROJECT_INIT_REAL_HELPERS` can select specific local tools. Standalone installer
tests exercise user/project scopes, complete payloads, and recovery after failures.

For a requested commit, review the exact diff and stage intended paths. Use a
descriptive message such as `fix: preserve custom documentation during sync`.
Follow the established branch/remote workflow and existing user authorization.

<a id="korean"></a>
## 한국어

[AGENTS.md](AGENTS.md)를 읽고 사용자 문서와 과거 릴리스를 보존합니다. 파일·Git
동작은 실제 자격 증명이나 원격 저장소 대신 임시 저장소로 검증합니다.
양언어 문서와 변경 이력을 갱신하고 영향받는 입력에 따라 검증을 선택합니다.

| 변경 | 필요한 범위 |
|---|---|
| 일반 문장·링크·배지 | 관련 문서·링크 검사; 애플리케이션 전체 테스트는 불필요 |
| 스킬 지침·템플릿 | 문서 검사와 영향받은 동작 시나리오 |
| Python·설치·검사·패키징 동작 | 관련 도우미 테스트; 공통 동작이나 규칙상 필요할 때 확대 |
| 릴리스 | `make test`, `make check`, `make package` |

입력이 같은 유효한 결과는 출처를 기록하고 재사용합니다. 같은 범위의 검사·리뷰는
한 담당자가 수행합니다. 마지막 소스·문서 편집 후 배포 파일을 다시 만들고,
입력이 같으면 그 빌드도 재사용합니다. 생성된 ZIP은 직접 수정하지 않습니다.
[검증 범위와 재사용](skills/project-init/references/verification.md)을 참고합니다.

검사 도구 테스트는 실제 임시 Git 저장소와 파일 접근 경계를 확인합니다. 설치
테스트는 임시 사용자 디렉터리와 통제된 CLI 동작을 사용하며, 패키징 테스트는
두 배포 파일을 압축 해제해 내용을 확인합니다. 스킬 지침을 변경하면
[동작 시나리오](docs/reference/skill-evaluation.md) 중 영향받은 항목을 수행하고 실제 결과,
기존 내용 보존, 반복 실행 동작을 검토합니다.

설치·CLI 연동을 변경했거나 릴리스에서 요구할 때 Codex와 plugin-creator
도우미를 사용하는 선택적 통합 검증을 실행합니다.

```bash
PROJECT_INIT_REAL_INTEGRATION=1 make test
```

임시 프로필과 번들 도우미를 사용하며 압축을 해제한 로컬 목록으로 플러그인
설치·갱신도 검증합니다. 실제 자격 증명이나 사용 중인 프로필은 사용하지 않습니다.
`PROJECT_INIT_REAL_CODEX`, `PROJECT_INIT_REAL_HELPERS`로 로컬 도구를 선택합니다.
단독 스킬 설치 테스트는 사용자·프로젝트 범위, 전체 리소스, 실패 후 복구를
확인합니다.

커밋을 요청받으면 실제 차이를 검토하고 의도한 파일만 스테이징합니다.
`fix: preserve custom documentation during sync`처럼 변경을 설명하는 메시지를
사용합니다. 기존 브랜치·원격 저장소 작업 방식과 사용자 권한을 따릅니다.
