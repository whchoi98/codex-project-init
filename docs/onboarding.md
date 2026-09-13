# Onboarding

<a href="#english">English</a> · <a href="#korean">한국어</a>

<a id="english"></a>
## English

Local development uses Python 3.9+ and Git. The auditor and tests use the standard
library. Installation also requires a Codex CLI with plugin support and its
bundled plugin-creator helpers.

```bash
make test
make check
make package
python3 scripts/install.py --dry-run
```

Read the [skill entrypoint](../skills/project-init/SKILL.md). Use temporary projects
for [behavior trials](reference/skill-evaluation.md). Review
[auditor profiles and coverage](reference/auditor.md) before applying checks to
another project. For a local installation, follow the
[release/install runbook](runbooks/release.md) and open a new Codex thread afterward.
Preview intentional replacements with `--dry-run --replace`.

A source export without Git metadata receives a warning from ordinary `check`;
`check --for-commit` treats missing Git metadata as a blocker.

<a id="korean"></a>
## 한국어

로컬 개발에는 Python 3.9 이상과 Git이 필요하며 검사 도구와 테스트는 표준
라이브러리를 사용합니다. 설치에는 플러그인을 지원하는 Codex CLI와 번들
plugin-creator 도우미도 필요합니다.

```bash
make test
make check
make package
python3 scripts/install.py --dry-run
```

[스킬 진입점](../skills/project-init/SKILL.md)을 읽고 임시 프로젝트로
[동작 시나리오](reference/skill-evaluation.md)를 검증합니다. 다른 프로젝트를
점검하기 전에 [검사 프로필과 범위](reference/auditor.md)를 확인합니다. 로컬
설치는 [릴리스·설치 런북](runbooks/release.md)을 따르고 설치 후 새 Codex 대화를
엽니다. 의도한 교체는 `--dry-run --replace`로 미리 확인합니다.

Git 메타데이터가 없는 소스 사본은 일반 `check`에서 경고를 받습니다.
`check --for-commit`에서는 Git 메타데이터 부재를 차단 사유로 처리합니다.
