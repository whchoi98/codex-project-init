# Contributing

<a href="#english">English</a> · <a href="#korean">한국어</a>

<a id="english"></a>
## English

Read [AGENTS.md](AGENTS.md). Preserve custom documentation and historical releases.
Test filesystem and Git behavior with temporary repositories, not live credentials
or remotes. Run `make test`, `make check`, and `make package`; update both public
language sections and the changelog. Do not edit generated ZIPs.

Auditor tests exercise real temporary Git repositories and filesystem boundaries.
Installation tests use temporary homes and controlled CLI behavior. Packaging
tests extract both artifacts and check their content. For skill instruction
changes, run the [behavior trials](docs/reference/skill-evaluation.md) and inspect
actual outputs, preservation, and repeated-run behavior.

With Codex and its plugin-creator helpers installed, enable the optional
integration trials:

```bash
PROJECT_INIT_REAL_INTEGRATION=1 make test
```

These trials use scratch profiles and CLI help; they do not install a live
plugin or use credentials. `PROJECT_INIT_REAL_CODEX` and
`PROJECT_INIT_REAL_HELPERS` can select specific local tools.

For a requested commit, review the exact diff and stage intended paths. Use a
descriptive message such as `fix: preserve custom documentation during sync`.
Follow the established branch/remote workflow and existing user authorization.

<a id="korean"></a>
## 한국어

[AGENTS.md](AGENTS.md)를 읽고 사용자 문서와 과거 릴리스를 보존합니다. 파일·Git
동작은 실제 자격 증명이나 원격 저장소 대신 임시 저장소로 검증합니다.
`make test`, `make check`, `make package`를 실행하고 양언어 문서와 변경 이력을
갱신합니다. 생성된 ZIP은 직접 수정하지 않습니다.

검사 도구 테스트는 실제 임시 Git 저장소와 파일 접근 경계를 확인합니다. 설치
테스트는 임시 사용자 디렉터리와 통제된 CLI 동작을 사용하며, 패키징 테스트는
두 배포 파일을 압축 해제해 내용을 확인합니다. 스킬 지침을 변경하면
[동작 시나리오](docs/reference/skill-evaluation.md)를 수행하고 실제 결과,
기존 내용 보존, 반복 실행 동작을 검토합니다.

Codex와 plugin-creator 도우미가 설치되어 있다면 선택적인 통합 검증도 실행합니다.

```bash
PROJECT_INIT_REAL_INTEGRATION=1 make test
```

임시 프로필과 CLI 도움말을 사용하며 실제 플러그인을 설치하거나 자격 증명을
사용하지 않습니다. `PROJECT_INIT_REAL_CODEX`, `PROJECT_INIT_REAL_HELPERS`로
특정 로컬 도구를 선택할 수 있습니다.

커밋을 요청받으면 실제 차이를 검토하고 의도한 파일만 스테이징합니다.
`fix: preserve custom documentation during sync`처럼 변경을 설명하는 메시지를
사용합니다. 기존 브랜치·원격 저장소 작업 방식과 사용자 권한을 따릅니다.
