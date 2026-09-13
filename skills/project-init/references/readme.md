# README authoring and synchronization

## English

Use this contract when creating or updating a README, including initialization
and `sync-docs`. First select the structure in [document conventions](documents.md).
For new bilingual files or requested format adoption, adapt
[the README template](../assets/readme.md). For an existing custom document,
map these content roles to its existing headings.

### Evidence and header

Read the real entrypoints, manifests, license, documented public contacts,
tests, and CI configuration. Record only established repository/demo links.
Example placeholders in a request are examples, not project metadata.

The header contains, in order:

1. `# PROJECT_NAME`.
2. One row of Shields badges: license, build status, version, English, 한국어.
3. A one-line English description and its Korean equivalent.
4. `---`, then `# English`; separate `# 한국어` with another `---`.

Language badges link to `#english` and `#한국어`. Use meaningful image alt text.
GitHub supplies those anchors from the language headings; retain a legacy custom
anchor when needed to preserve an existing incoming link.

| Badge | Evidence and fallback |
|---|---|
| License | Read the license/manifest; link the actual license file. If absent, use a neutral `license-not_specified-lightgrey` badge with no invented file link |
| Build | Use a Shields dynamic badge for an actual workflow and branch. If no CI is configured, use `build-not_configured-lightgrey`; a local test run does not establish hosted CI status |
| Version | Use the authoritative manifest or supplied release version. A static `version-VERSION-blue` badge can link that manifest; use `version-not_specified-lightgrey` if unknown |
| Languages | Use Shields images with Markdown links to the language anchors |

All badge images use `https://img.shields.io/`. Encode label/message text using
[Shields syntax](https://shields.io/badges/static-badge): `_` is a space, `__` a
literal underscore, and `--` a literal hyphen. Encode other URL-sensitive text.
Link badges with Markdown; the image URL's `link=` option is not a Markdown link.

### Ordered sections

Keep the following order in each language. Custom sections retain their content
and useful position relative to these roles.

| English h2 | Korean h2 | Content and condition |
|---|---|---|
| Overview | 개요 | Required: purpose/problem in 2–3 sentences; include a supplied demo with useful alt text |
| Features | 주요 기능 | Required: `- **Feature** — description` for actual capabilities |
| Prerequisites | 사전 요구 사항 | Required: runtime/tool minimum versions from evidence |
| Installation | 설치 방법 | Required: stepwise `bash` commands with short comments; if no package installer exists, document the actual source-based workflow |
| Usage | 사용법 | Required: executable examples with observed or source-verified output |
| Configuration | 환경 설정 | Include when user-facing environment variables exist; table of name, description, default |
| Project Structure | 프로젝트 구조 | Recommended: `text` tree of real paths with localized comments; link architecture docs or include a small evidenced diagram here |
| Testing | 테스트 | Include when tests exist; full suite, specific-file and coverage commands only when supported |
| API Documentation | API 문서 | Include for an actual public API/contract; link its real reference. Private helpers do not imply a service API |
| Contributing | 기여 방법 | Required: Fork → Branch → Commit → Push → PR as a numbered procedure for a GitHub project, respecting CONTRIBUTING and branch rules |
| License | 라이선스 | Required: actual license name and file link; otherwise state that no license is supplied |
| Contact | 연락처 | Required: declared maintainer profile, established Issues URL, and explicitly public email when available |

For missing optional contact fields, state what is unavailable and use the
known channel. Do not infer public contact email from local Git configuration.
For a project without a GitHub repository, describe the available contribution
handoff instead of inventing fork/PR URLs. Conventional Commit examples such as
`feat: add CSV export` or `fix: handle empty input` accompany the commit step
unless the target explicitly uses another convention.

Every code fence has the appropriate language: `bash` for shell commands and
the implementation language for API/code examples. Match command tokens, output, variable/default
cells, paths, and diagram labels across languages. Translate explanations and
comments, including tree comments. Use polite Korean sentences, concise English
instructions, and no emoji. Omit unsupported coverage commands and inapplicable
Configuration/API sections; state a missing test capability briefly when useful.

### Update and verify

Update the existing section that owns a changed fact. Keep paired sections and
their order, preserve operator notes and existing useful links, and refresh both
languages together. Rebuild a tree only when paths change; do not rewrite prose
or insert empty optional sections on a repeat sync.

Review the header, section sequence, bilingual meaning, code/output equality,
local paths/anchors, badge sources, and absence of leftover template variables.
Run applicable project checks within the authoring scope and report actual
results separately from detected commands.

## 한국어

초기화와 `sync-docs`를 포함해 README를 작성·갱신할 때 사용합니다.
[문서 규칙](documents.md)에서 구조를 먼저 선택합니다. 새 이중 언어 문서나
명시적인 형식 전환에는 [README 템플릿](../assets/readme.md)을 사용하고,
기존 사용자 정의 문서는 아래 역할을 현재 헤딩에 대응시킵니다.

### 근거와 최상단

실제 진입점·매니페스트·라이선스·공개 연락처·테스트·CI를 확인합니다.
요청에 들어 있는 예시 값은 프로젝트의 사실로 사용하지 않습니다.

최상단은 프로젝트명 h1, 라이선스·빌드·버전·영어·한국어 Shields 배지 한 줄,
영어와 한국어 한 줄 설명, 수평선, `# English` 순서로 작성합니다.
다음 언어 블록은 수평선과 `# 한국어`로 시작합니다. 언어 배지의 링크는
`#english`, `#한국어`이며 의미 있는 대체 텍스트를 제공합니다.
기존 유입 링크에 필요한 사용자 정의 앵커는 보존합니다.

라이선스는 실제 파일을 연결하고, 없으면 `not specified` 중립 배지로
표시합니다. 실제 CI가 있어야 동적 빌드 배지를 사용하며, 없으면
`not configured`로 표시합니다. 로컬 테스트 성공을 CI 상태로 표시하지
않습니다. 버전은 매니페스트나 제공된 릴리스 정보를 사용하고, 없으면
`not specified`로 표시합니다. 배지 이미지는 모두 `img.shields.io`를
사용하고 클릭 대상은 Markdown 링크로 지정합니다.
[Shields 문법](https://shields.io/badges/static-badge)에 따라 `_`는 공백,
`__`는 밑줄, `--`는 하이픈을 나타내며 그 밖의 URL 특수 문자도 인코딩합니다.

### 섹션 순서와 내용

영어 블록의 표와 같은 순서로 다음 h2를 배치합니다.

| 영어 | 한국어 | 조건과 내용 |
|---|---|---|
| Overview | 개요 | 필수: 목적·문제를 2–3문장으로 설명하며 제공된 데모 포함 |
| Features | 주요 기능 | 필수: `- **기능명** — 설명` 형식의 실제 기능 |
| Prerequisites | 사전 요구 사항 | 필수: 확인된 런타임·도구·최소 버전 |
| Installation | 설치 방법 | 필수: 단계별 주석이 있는 bash 명령; 실제 소스 실행 방식도 가능 |
| Usage | 사용법 | 필수: 실행 가능한 예제와 확인된 출력 |
| Configuration | 환경 설정 | 사용자용 환경 변수가 있을 때 변수명·설명·기본값 표 |
| Project Structure | 프로젝트 구조 | 권장: 실제 경로의 text 트리와 설명; 실제 아키텍처 링크·다이어그램 |
| Testing | 테스트 | 테스트가 있을 때 실제 전체·개별 테스트·커버리지 명령 |
| API Documentation | API 문서 | 공개 API·계약이 있을 때 실제 참조 문서 연결 |
| Contributing | 기여 방법 | 필수: 저장소 정책을 반영한 Fork → Branch → Commit → Push → PR |
| License | 라이선스 | 필수: 실제 라이선스와 파일 링크, 없으면 미제공 사실 |
| Contact | 연락처 | 필수: 알려진 유지관리자·Issues·명시적으로 공개된 이메일 |

사용자 정의 섹션은 내용을 보존하고 관련 역할 주변의 위치를 유지합니다.
비공개 도우미 함수만으로 서비스 API를 가정하지 않습니다. 연락처 일부가
없으면 알려진 경로를 안내하고 없는 항목을 간단히 표시합니다. 로컬 Git
설정의 이메일을 공개 연락처로 추정하지 않습니다. GitHub 저장소가 없으면
실제 기여 전달 방법을 설명합니다. 별도 커밋 정책이 없다면 Commit 단계에
`feat: add CSV export`, `fix: handle empty input` 같은 예시를 포함합니다.

코드 펜스는 셸 명령에 `bash`, API·코드 예제에 실제 구현 언어를 지정합니다.
실행 구문·출력·변수·기본값·경로·다이어그램
레이블은 양쪽에서 같게 유지하고 설명·주석·트리 주석을 번역합니다.
한국어는 경어체, 영어는 간결한 실행 지침을 사용하며 이모지는 넣지 않습니다.
지원하지 않는 커버리지 명령이나 해당하지 않는 환경 설정·API 섹션은
생략합니다. 필요한 경우 없는 검증 기능을 짧게 설명합니다.

### 갱신과 검증

변경된 사실을 담당하는 기존 섹션을 수정하고, 양 언어의 순서·내용을 함께
갱신합니다. 운영 메모와 유효한 링크를 보존합니다. 경로 변화가 있어야 트리를
수정하며, 반복 동기화로 문장을 다시 쓰거나 빈 선택 섹션을 만들지 않습니다.

최상단·헤딩 순서·번역의 의미·코드와 출력·경로와 앵커·배지의 근거·미치환
변수를 확인합니다. 작성 범위에 맞는 검증을 실행하고, 실제 결과와 단순히
탐지한 명령을 구분해 보고합니다.
