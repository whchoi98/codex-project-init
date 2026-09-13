# Skill behavior trials

<a href="#english">English</a> · <a href="#korean">한국어</a>

<a id="english"></a>
## English

Python tests validate the helpers. Skill changes also need realistic authoring
and review trials: metadata validation alone cannot prove scope preservation,
semantic accuracy, or repeated-run behavior.

Generate fresh isolated projects without invoking a model or using credentials:

```bash
python3 tests/skill_trials.py
```

The [generator](../../tests/skill_trials.py) prints project paths and user requests.
Each project contains a standard-library CSV CLI and a test. The check fixture
uses a real local Git index with a synthetic private-key header; its working-tree
replacement is ordinary text. Hash snapshots live beside the projects.

Use the source skill at `skills/project-init/SKILL.md` in a fresh agent context
for each printed request. Limit that context's write scope to its fixture.
Provide the request and raw project, without telling the agent the expected
answer. Inspect the resulting files and output afterward.

| Trial | Evidence to verify afterward |
|---|---|
| README only | Correct entrypoint, required `--column`, and sample output; custom Korean operator note and released changelog preserved; unrelated files unchanged |
| Read-only check | Broken local link, unsupported option, wrong command, and index-only key header identified; no matching secret value disclosed; file/index hashes unchanged; project tests not run |
| Initialization | Useful English/Korean project docs from the CLI; original application files retained; no fabricated service, license, release history, or Git setup |

For authoring trials, save hashes after the first result. Reapply the README
request, or follow initialization with a sync request, without changing the
code. Compare documents against those saved hashes; a repeat should not cause
unnecessary edits. Distinguish generated Python caches from authored documents
when examining an authoring run.

Record actual commands and results, including missing Git or incomplete audit
coverage. These are qualitative regression trials, not a numerical skill score.
Clean up only the generated temporary directory after reviewing its artifacts.

<a id="korean"></a>
## 한국어

Python 테스트는 도우미를 검증합니다. 스킬 변경에는 실제 작성·검토 시나리오도
필요합니다. 메타데이터 검증만으로 요청 범위 보존, 내용의 정확성, 반복 실행
동작을 입증할 수는 없습니다.

모델을 호출하거나 자격 증명을 사용하지 않고 새로운 격리 프로젝트를 생성합니다.

```bash
python3 tests/skill_trials.py
```

[생성 도구](../../tests/skill_trials.py)가 프로젝트 경로와 사용자 요청을 출력합니다.
각 프로젝트에는 표준 라이브러리 CSV CLI와 테스트가 있습니다. 점검용 프로젝트는
합성 개인 키 헤더가 들어 있는 실제 로컬 Git 인덱스를 사용하며 작업 파일은 일반
텍스트로 교체되어 있습니다. 해시 스냅샷은 프로젝트 옆에 저장합니다.

각 요청을 새 에이전트 문맥에서 소스 스킬 `skills/project-init/SKILL.md`로
수행합니다. 쓰기 범위는 해당 임시 프로젝트로 제한합니다. 예상 답을 알려주지
않고 사용자 요청과 프로젝트 원본을 전달한 다음, 실제 결과 파일과 출력을
검토합니다.

| 시나리오 | 작업 후 확인할 근거 |
|---|---|
| README만 수정 | 올바른 진입점·필수 `--column`·예제 출력, 한국어 운영 메모와 릴리스 이력 보존, 관련 없는 파일 유지 |
| 읽기 전용 점검 | 깨진 링크·지원하지 않는 옵션·잘못된 명령·인덱스에만 있는 키 헤더 탐지, 비밀 값 비공개, 파일·인덱스 해시 유지, 프로젝트 테스트 미실행 |
| 초기화 | CLI에 근거한 유용한 영어·한국어 문서, 기존 코드 보존, 서비스·라이선스·릴리스 이력·Git 설정을 만들어 내지 않음 |

작성 시나리오는 첫 결과의 해시를 저장합니다. 코드를 변경하지 않고 README
요청을 반복하거나 초기화 뒤 동기화를 요청합니다. 저장한 해시와 문서를 비교해
불필요한 수정이 없는지 확인합니다. 작성 작업을 살펴볼 때는 Python이 생성한
캐시와 작성된 문서를 구분합니다.

실제 실행한 명령과 결과를 기록하고 Git 부재나 불완전한 검사 범위도 포함합니다.
이 시나리오는 정성적인 회귀 검증이며 수치형 스킬 점수가 아닙니다. 결과 검토
후에는 생성한 임시 디렉터리만 정리합니다.
