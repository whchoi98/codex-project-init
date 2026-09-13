# Changelog

<a href="#english">English</a> · <a href="#korean">한국어</a>

<a id="english"></a>
# English

## [Unreleased]

### Added

- Add core/existing document profiles, explicit required document paths,
  conventional layout support, command provenance, and scan coverage details.
- Add repeatable skill trials for targeted authoring, read-only review, and
  initialization followed by synchronization.
- Add shared source/payload validation, reproducible distributions, and
  installation recovery tests.

### Changed

- Focus the skill on the requested documentation operation, preserve repeat-run
  stability, and separate semantic review from structural checks.
- Split the auditor into filesystem, document, project, and Git components while
  preserving its CLI and existing JSON fields.
- Build and install from the same explicit payload and validate complete skill
  resources before delivery.

### Fixed

- Prevent project-defined Git clean/process filters from executing during audit
  (including filter names with `=`), reject linked/external Git configuration,
  and keep Git checks within the requested subproject.
- Report unreadable, external, cyclic, special, and oversized files without
  hanging or silently claiming full coverage.
- Ignore inline code and comments in link checks, decode escaped destinations,
  and honor Git ignore rules for generated documents.
- Prepare installation candidates before replacing sources, retain backups,
  and report recovery limits when external Codex state may have changed.

## [0.1.0] - 2026-09-13

### Added

- Add Codex-native initialization, documentation sync, targeted document additions,
  and Git preparation workflows adapted from project-init 2.4.0.
- Add a read-only auditor for manifests, documentation links, Git metadata,
  whitespace checks, and limited staged secret indicators.
- Add self-contained plugin/skill packages and personal-marketplace installation.

<a id="korean"></a>
# 한국어

## [Unreleased]

### Added

- core/existing 문서 프로필, 필수 문서 경로 지정, 일반적인 대체 문서 구조,
  명령 출처와 검사 범위 정보 추가.
- 일부 문서 작성, 읽기 전용 검토, 초기화 후 동기화를 확인하는 반복 가능한
  스킬 시나리오 추가.
- 공통 소스·배포 대상 검증, 재현 가능한 배포 파일, 설치 복구 테스트 추가.

### Changed

- 요청한 문서 작업에 집중하도록 스킬을 정리하고 반복 실행의 안정성을 유지하며
  내용 검토와 구조 검사를 분리.
- 기존 CLI와 JSON 필드를 유지하면서 검사 도구를 파일·문서·프로젝트·Git
  구성 요소로 분리.
- 동일한 명시적 배포 대상으로 빌드·설치하고 전체 스킬 리소스를 검증한 뒤 전달.

### Fixed

- 검사 중 프로젝트의 Git clean/process 필터 실행을 막고 Git 검사를 요청한
  하위 프로젝트 범위로 제한. 이름에 `=`가 있는 필터도 처리하고, 심볼릭 링크나
  외부 파일을 포함하는 Git 설정을 거부.
- 읽기 실패, 외부·순환 링크, 특수 파일, 큰 파일을 멈춤이나 완전한 검사로
  오인하는 결과 없이 보고.
- 링크 검사에서 인라인 코드·주석을 제외하고 이스케이프된 대상을 해석하며,
  생성 문서의 Git ignore 규칙 반영.
- 소스를 교체하기 전에 설치 후보를 준비하고 백업을 유지하며, 외부 Codex
  상태가 바뀌었을 수 있으면 복구 한계를 보고.

## [0.1.0] - 2026-09-13

### Added

- project-init 2.4.0 기반 Codex용 초기화, 문서 동기화, 개별 문서 추가,
  Git 준비 작업 추가.
- 메타데이터, 문서 링크, Git 상태, 공백 오류, 일부 스테이징 시크릿 징후를
  확인하는 읽기 전용 검사 도구 추가.
- 플러그인·단독 스킬 패키지와 개인 마켓플레이스 설치 기능 추가.
