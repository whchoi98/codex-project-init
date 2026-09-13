# ADR-001: Codex-native documentation workflows

[![English](https://img.shields.io/badge/lang-English-blue)](#english) [![한국어](https://img.shields.io/badge/lang-%ED%95%9C%EA%B5%AD%EC%96%B4-red)](#한국어)

<a id="english"></a>
## English

**Status:** Accepted, 2026-09-13.

The user requested a Codex counterpart to the existing Claude project-init,
especially README, changelog, documentation structure, and Git preparation.
The maintained Claude source is 2.4.0 and includes runtime-specific hook/config
contracts as well as reusable document conventions.

Use one routed Codex skill with focused references, applicable templates, and a
read-only auditor. Use AGENTS.md for project instructions. Preserve the original
bilingual/Mermaid approach for new public docs and preserve existing conventions.
Do not automatically copy Claude hooks, generic agents, or permission policies.

This keeps documentation tasks directly usable in Codex while making integration
migration explicit. The auditor supplies concrete findings; semantic quality,
translation parity, and actual test execution remain part of the agent workflow.

<a id="korean"></a>
## 한국어

**상태:** 승인됨, 2026-09-13.

사용자는 기존 Claude project-init의 Codex 버전을 요청했으며, 특히 README,
변경 이력, 문서 구조, Git 준비 작업이 필요합니다. 유지보수 중인 Claude 소스는
2.4.0이고, 재사용 문서 규칙과 런타임별 훅·설정 규칙이 함께 들어 있습니다.

작업을 분기하는 Codex 스킬과 참조 문서, 적용 가능한 템플릿, 읽기 전용 검사
도구로 구성합니다. 프로젝트 지침에는 AGENTS.md를 사용합니다. 새 공개 문서는
양언어·Mermaid 방식을 따르며 기존 문서 규칙을 보존합니다. Claude 훅, 범용
에이전트, 권한 정책을 자동 복사하지 않습니다.

문서 작업을 Codex에서 바로 사용할 수 있고, 연동 전환은 명시적으로 검토할 수
있습니다. 검사 도구는 구체적인 발견 사항을 제공하며 내용 정확성, 번역 일치,
실제 테스트 실행은 에이전트 작업에서 확인합니다.
