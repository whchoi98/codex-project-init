# Changelog

[![English](https://img.shields.io/badge/lang-English-blue)](#english) [![한국어](https://img.shields.io/badge/lang-%ED%95%9C%EA%B5%AD%EC%96%B4-red)](#한국어)

---

# English

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

No Git release tags are present, so version headings have no release or
comparison links.

## [Unreleased]

### Added

- Add native GitHub plugin installation through a validated, self-contained
  marketplace catalogue.
- Add standalone skill installation for user and project scopes, with previews,
  replacement backups, and failure recovery.
- Add structured bilingual README and changelog guides and templates for
  initialization and synchronization.
- Add `sync-doc` as an alias for documentation synchronization.
- Add core/existing document profiles, explicit required document paths,
  conventional layout support, command provenance, and scan coverage details.
- Add reproducible plugin and standalone skill distributions.

### Changed

- Use Shields language badges consistently across public documentation and
  document templates while preserving existing headings and anchors.
- Focus the skill on the requested documentation operation, preserve repeat-run
  stability, and separate semantic review from structural checks.
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

---

<a id="korean"></a>
# 한국어

이 프로젝트의 모든 주요 변경 사항은 이 파일에 기록됩니다.
이 문서는 [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)를 기반으로 하며,
[Semantic Versioning](https://semver.org/spec/v2.0.0.html)을 따릅니다.

Git 릴리스 태그가 없어 버전 헤딩에는 릴리스·비교 링크를 제공하지 않습니다.

## [Unreleased]

### Added

- 검증된 자체 포함 마켓플레이스 목록을 통한 GitHub 플러그인 설치 추가.
- 미리보기·교체 백업·실패 복구를 지원하는 사용자·프로젝트 범위 단독 스킬
  설치 추가.
- 초기화와 동기화를 위한 구조화된 이중 언어 README·변경 이력 작성 지침과
  템플릿 추가.
- 문서 동기화 별칭 `sync-doc` 추가.
- core/existing 문서 프로필, 필수 문서 경로 지정, 일반적인 대체 문서 구조,
  명령 출처와 검사 범위 정보 추가.
- 재현 가능한 플러그인·단독 스킬 배포 파일 추가.

### Changed

- 기존 헤딩과 앵커를 보존하면서 공개 문서·문서 템플릿의 언어 전환 표시를
  Shields 배지로 통일.
- 요청한 문서 작업에 집중하도록 스킬을 정리하고 반복 실행의 안정성을 유지하며
  내용 검토와 구조 검사를 분리.
- 동일한 명시적 배포 대상으로 빌드·설치하고 전체 스킬 리소스를 검증한 뒤 전달.

### Fixed

- 이름에 `=`가 있는 필터를 포함한 Git clean/process 필터 실행 차단,
  요청한 하위 프로젝트 범위 유지, 심볼릭 링크·외부 파일을 포함한 Git 설정 거부.
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
