# CHANGELOG authoring and synchronization

## English

Use this contract for initialization, changelog requests, affected `sync-docs`,
and requested release preparation. Select the structure through
[document conventions](documents.md), then adapt
[the CHANGELOG template](../assets/changelog.md) for a new file or requested
format adoption. Preserve existing custom layouts and historical entries.

### Format

Start with `# Changelog`, one row of Shields language badges linking to
`#english` and `#한국어`, a horizontal rule, then `# English`.
Put another horizontal rule before `# 한국어`.

Each language block has its localized Keep a Changelog/SemVer notice,
`## [Unreleased]`, then supplied releases newest first as
`## [VERSION] - YYYY-MM-DD`. The template contains the requested notices.
Use them when SemVer is the project's policy or is explicitly being adopted.
For a conflicting established version scheme, name the actual scheme instead
of claiming SemVer compliance.

Use identical versions, dates, category order, links, and change meanings in
both languages. Category h3 names stay English:

| Category | Meaning |
|---|---|
| Added | New user-facing capabilities |
| Changed | Changes to existing behavior |
| Deprecated | Features scheduled for removal |
| Removed | Features actually removed |
| Fixed | Corrected defects |
| Security | Vulnerability fixes |

Use that category order and omit categories without entries. Keep Unreleased
even when empty. Each bullet describes one concrete user-visible change in one
sentence. Begin English entries with an action verb; use Korean noun endings.
Prefix incompatible changes with `**BREAKING:**` in both languages and describe
the migration impact. Append real issue/PR links when supplied or established.

Group commits by their effect on users. Do not copy commit logs, duplicate a
change across categories, use vague fix summaries, or add internal refactors
and tests with no user-visible effect. Preserve existing published descriptions,
categories, dates, yanked markers, and release-specific evidence.

### Version links

Maintain one shared reference-definition block at the end of the file. Both
language blocks use the same version labels. Markdown definitions apply to the
whole document; a single block avoids divergent duplicate definitions.

For an established GitHub remote and evidenced release refs:

- `[Unreleased]` compares the latest released ref to `HEAD`.
- Each later release compares the preceding release ref to its own ref.
- The first release links to its actual tag/release page, since it has no
  preceding release to compare.

Use the real tag prefix, including no prefix when that is the project's
convention. A manifest version or dated heading alone does not prove a tag
exists. If refs are unknown, retain plain bracketed headings without definitions
and explain the missing comparison information briefly in both languages.
Keep any already established valid definitions.

A user-requested release may explicitly plan a future tag. Comparison links
may use that supplied planned ref, with publication readiness reported clearly.
Do not create tags or publish releases as a side effect of writing the document.

### Synchronization and releases

During ordinary sync, map actual user-visible changes to the existing
Unreleased categories and update both languages together. Deduplicate by meaning;
a translation or formatting adjustment is not another product change.
Keep released blocks intact and preserve unrelated pending items. A second
sync with unchanged evidence leaves the file unchanged.

For a release request:

1. Establish the requested version, date, included changes, and tag convention.
   Do not infer a release from the current date or manifest version.
2. Move only the selected Unreleased entries into the new dated version in each
   language. Leave other pending items in Unreleased; leave it empty when all
   pending work is released.
3. Refresh shared comparison definitions from the evidenced/planned refs.
4. Verify older entries are unchanged and the two language blocks agree.

Respect [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html) when selecting a
requested release: after 1.0.0, incompatible public API changes require a major
increment, compatible additions/deprecations a minor increment, and compatible
fixes a patch increment. For `0.y.z`, follow the project's initial-development
policy. Preserve prerelease/build metadata. Flag conflicts with a supplied version
rather than silently changing it. Version-file edits and Git operations follow
their own authorized scope.

### Review

Compare both language blocks' release sequence, dates, categories, breaking
markers, and entry meanings. Check ISO dates, unique reference definitions,
known link targets, preserved historical content, and absence of empty category
headings or template variables. Structural helper checks do not prove these facts.
See [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/).

## 한국어

초기화, 변경 이력 작성, 관련 `sync-docs`, 요청받은 릴리스 준비에 적용합니다.
[문서 규칙](documents.md)에 따라 구조를 선택한 뒤 새 문서나 명시적인 형식
전환에는 [CHANGELOG 템플릿](../assets/changelog.md)을 사용합니다.
기존 사용자 정의 구조와 과거 항목을 보존합니다.

### 형식

`# Changelog`, `#english`·`#한국어`로 연결하는 Shields 언어 배지 한 줄,
수평선, `# English` 순서로 시작합니다. `# 한국어` 앞에도 수평선을 넣습니다.

각 언어 블록에는 해당 언어의 Keep a Changelog·SemVer 안내 문구,
`## [Unreleased]`, 최신순 릴리스 `## [VERSION] - YYYY-MM-DD`를 배치합니다.
템플릿의 안내 문구는 SemVer를 따르거나 명시적으로 채택하는 프로젝트에
사용합니다. 다른 버전 정책이 이미 있으면 실제 정책을 설명합니다.

버전·날짜·카테고리 순서·링크·변경의 의미를 양쪽에서 일치시킵니다.
h3 카테고리는 아래 영어 이름과 순서를 그대로 사용하고 빈 카테고리는 생략합니다.

| 카테고리 | 의미 |
|---|---|
| Added | 사용자에게 제공하는 새 기능 |
| Changed | 기존 동작 변경 |
| Deprecated | 향후 제거 예정 |
| Removed | 실제 제거 |
| Fixed | 결함 수정 |
| Security | 보안 취약점 수정 |

Unreleased는 비어 있어도 유지합니다. 불릿 하나에 구체적인 사용자 대상 변경
하나를 한 문장으로 기록합니다. 영어는 동사로 시작하고 한국어는 명사형으로
끝냅니다. 호환되지 않는 변경에는 양쪽 모두 `**BREAKING:**`을 붙이고
전환 시 영향을 설명합니다. 확인된 이슈·PR 링크가 있으면 항목 끝에 넣습니다.

커밋을 사용자에게 미치는 효과로 묶습니다. 커밋 로그 복사, 여러 카테고리의
중복 기록, 모호한 수정 설명, 사용자 영향이 없는 내부 리팩토링·테스트 기록은
추가하지 않습니다. 기존 공개 항목의 설명·카테고리·날짜·배포 철회 표시·
릴리스별 검증 기록은 보존합니다.

### 버전 링크

파일 맨 아래의 공통 참조 정의를 한 번만 관리하고 양 언어가 같은 버전
레이블을 사용합니다. Markdown 참조 정의는 문서 전체에 적용되므로 중복
정의를 두지 않아도 양쪽 버전 헤딩이 같은 주소를 가리킵니다.

GitHub 원격과 릴리스 ref가 확인됐다면 Unreleased는 최신 릴리스 ref에서
HEAD까지, 이후 릴리스는 직전 ref에서 해당 ref까지 비교합니다.
첫 릴리스는 비교할 이전 버전이 없으므로 실제 태그·릴리스 페이지를 연결합니다.

실제 태그 접두사나 접두사 없는 관례를 따릅니다. 매니페스트 버전이나 날짜가
있는 헤딩만으로 태그 존재를 가정하지 않습니다. ref를 모르면 대괄호 헤딩을
일반 텍스트로 남기고 양 언어에서 비교 정보가 부족함을 짧게 설명합니다.
이미 확인된 유효한 링크 정의는 유지합니다.

사용자가 릴리스와 향후 태그를 명시적으로 계획했다면 그 ref를 비교 링크에
사용할 수 있으며, 공개 전 상태를 분명하게 보고합니다. 문서 작성만으로
태그를 만들거나 릴리스를 공개하지 않습니다.

### 동기화와 릴리스

일반 동기화에서는 실제 사용자 대상 변경을 Unreleased에 대응시켜 양쪽을
갱신합니다. 의미를 기준으로 중복을 제거하며 번역·형식 수정을 별도 제품
변경으로 추가하지 않습니다. 공개된 블록과 무관한 미공개 항목을 유지하고,
근거가 같으면 반복 동기화에서도 파일을 그대로 유지합니다.

릴리스 요청에서는 다음 순서로 처리합니다.

1. 요청한 버전·날짜·포함할 변경·태그 관례를 확인합니다. 현재 날짜나
   매니페스트 버전만으로 릴리스를 만들지 않습니다.
2. 양쪽 Unreleased에서 해당 항목만 새 날짜·버전 블록으로 옮깁니다.
   남은 항목은 유지하고 전부 포함됐다면 Unreleased를 비워 둡니다.
3. 확인되거나 명시적으로 계획된 ref로 공통 비교 링크를 갱신합니다.
4. 과거 항목 보존과 양 언어의 일치 여부를 확인합니다.

[SemVer 2.0.0](https://semver.org/spec/v2.0.0.html)에 따라 1.0.0 이후에는
공개 API 비호환 변경은 major, 호환되는 기능 추가·폐기 예고는 minor,
호환되는 결함 수정은 patch를 올립니다. `0.y.z`는 프로젝트의 초기 개발
정책을 따르고 prerelease·build 메타데이터는 보존합니다. 제공된 버전과
충돌하면 알리고 임의로 바꾸지 않습니다. 버전 파일 수정과 Git 작업에는
별도의 허용 범위를 적용합니다.

### 검토

양 언어의 릴리스 순서·날짜·카테고리·BREAKING 표시·항목 의미를 비교합니다.
ISO 날짜, 중복 없는 참조 정의, 확인된 링크, 과거 내용 보존, 빈 카테고리와
미치환 변수의 부재를 확인합니다. 구조 검사 도구만으로 이 사실을 입증할 수는
없습니다. [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/)을
참고합니다.
