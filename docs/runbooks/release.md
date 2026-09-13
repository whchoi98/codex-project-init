# Release and Local Installation

[![English](https://img.shields.io/badge/lang-English-blue)](#english) [![한국어](https://img.shields.io/badge/lang-%ED%95%9C%EA%B5%AD%EC%96%B4-red)](#한국어)

<a id="english"></a>
## English

1. Review source and documentation changes. Update `.codex-plugin/plugin.json`
   and the changelog when preparing a release; preserve older entries.
2. Run the following from the repository root:

```bash
make test
make check
make package
python3 scripts/validate_distribution.py
```

3. Verify `dist/manifest.json` checksums and both ZIP contents. The validation
   command checks metadata, selected payload, and agreement with current source.
   The plugin archive contains this source package and its native marketplace
   catalogue; the standalone archive
   contains the entire `project-init` folder, including its sibling Python
   implementation package, references, and assets. Rebuild after the last edit.
4. Choose a [skill or plugin installation](../../README.md#installation).
   Use the selected local mode's `--dry-run` before installation and add
   `--replace` for an intentional update with a retained backup.
5. Open a new Codex thread and verify that Project Init is discoverable.

### Installation modes

Native GitHub plugin installation uses this repository's
[catalogue](../../.agents/plugins/marketplace.json):

```bash
codex plugin marketplace add whchoi98/codex-project-init --ref main
codex plugin add codex-project-init@codex-project-init
```

Refresh with `codex plugin marketplace upgrade codex-project-init`, then repeat
`codex plugin add`. This uses Codex's marketplace/cache lifecycle.

The local Python entrypoint keeps plugin mode as its default:

| Mode | Destination | Requirements |
|---|---|---|
| `--mode skill` | `~/.agents/skills/project-init` | Python 3.9+ and directory-descriptor APIs, such as Linux/macOS |
| `--mode skill --project PATH` | `PATH/.agents/skills/project-init` | Same, plus an existing real project directory |
| `--mode plugin` or omitted | `~/plugins/codex-project-init` and the personal marketplace | Codex CLI and bundled plugin-creator helpers |

Both local modes support `--dry-run` and `--replace`. `--project` is skill-only;
`--codex /absolute/path/to/codex` is plugin-only and selects a compatible CLI
when PATH differs. A standalone installation copies the entire skill from
validated captured bytes and does not register a marketplace.
Use the [Codex skill installation request](../../README.md#standalone-skill)
when installing directly from GitHub or when descriptor APIs are unavailable.
Unsupported local skill platforms fail preflight before writing.

### Build and recovery

Packaging selects maintained source roots and excludes credential-oriented
filenames, caches, and unrelated root files. The native catalogue is an explicit
payload file; other `.agents` state stays excluded. Its plugin name, root source,
and policies are validated. Packaging does not scan allowed file
contents for secrets. Included symlinks and special files are
rejected. ZIP order, timestamps, and file modes are normalized; unchanged inputs
produce the same checksums with the same Python/compression tooling. The builder
validates a candidate before publication and restores existing artifacts if a
handled publication failure occurs.

The local plugin installer uses Codex's scaffold, cachebuster, and `plugin add` flow. Its dry
run performs source/path/helper/CLI preflight and prints the selected executable
and destination. It requires the source checkout to be separate from the
installation destination.

Before replacing a plugin source, the installer prepares and validates a complete
candidate. Successful replacements leave a timestamped source backup beside
the destination, with the exact path printed in the result. On a handled
replacement failure, the previous source is restored.

If a first installation fails after publishing a marketplace entry, a complete
source is retained so the entry does not point at a missing directory. Review
the reported state and preview a retry with `--dry-run --replace`. The installer
does not claim to roll back Codex's marketplace/cache effects. Follow any
reported recovery path if automatic source restoration fails. Child output is
withheld from diagnostics; the operation and exit status identify the failed step.

Skill mode also prepares a complete candidate before publishing. A replacement
retains the whole previous skill directory, including custom files, at the
reported backup path. Follow the reported recovery paths if another process
changes the destination or automatic restoration fails. Abrupt termination is
not a completed rollback; inspect retained installation/backup directories before
retrying. Never discard a backup until the intended installation has been verified.
If an ancestor was moved, diagnostics identify the original path; verify where
the retained directory now resides before attempting manual recovery.

Publishing, tagging, pushing, and changing a live installation follow the user's
chosen destination and scope. An ordinary source validation does not install
anything. Before changing skill workflows, run the
[behavior trials](../reference/skill-evaluation.md).

<a id="korean"></a>
## 한국어

1. 소스·문서 변경을 검토합니다. 릴리스를 준비할 때 `.codex-plugin/plugin.json`과
   변경 이력을 갱신하며 과거 항목은 보존합니다.
2. 저장소 루트에서 실행합니다.

```bash
make test
make check
make package
python3 scripts/validate_distribution.py
```

3. `dist/manifest.json`의 체크섬과 두 ZIP 내용을 확인합니다. 검증 명령은
   메타데이터·배포 대상·현재 소스와의 일치 여부를 확인합니다. 플러그인 ZIP은
   이 소스 패키지와 GitHub 설치 목록을 포함하고, 단독 스킬 ZIP은 Python 구현 패키지·참조 문서·
   템플릿을 포함한 `project-init` 폴더 전체를 담습니다. 마지막 편집 후 다시
   빌드합니다.
4. [스킬 또는 플러그인 설치](../../README.md#설치-방법)를 선택합니다.
   로컬 설치는 해당 모드의 `--dry-run`으로 미리 확인하고, 의도한 갱신은
   `--replace`로 이전 설치본을 백업하며 교체합니다.
5. 새 Codex 대화에서 Project Init 스킬이 검색되는지 확인합니다.

### 설치 방식

GitHub 플러그인 설치는 이 저장소의
[목록](../../.agents/plugins/marketplace.json)을 사용합니다.

```bash
codex plugin marketplace add whchoi98/codex-project-init --ref main
codex plugin add codex-project-init@codex-project-init
```

`codex plugin marketplace upgrade codex-project-init`으로 갱신한 뒤
`codex plugin add`를 다시 실행합니다. 마켓플레이스와 캐시는 Codex가 관리합니다.

로컬 Python 진입점의 기본값은 기존과 같은 플러그인 모드입니다.

| 모드 | 설치 위치 | 요구 사항 |
|---|---|---|
| `--mode skill` | `~/.agents/skills/project-init` | Python 3.9 이상과 Linux/macOS 등의 디렉터리 디스크립터 API |
| `--mode skill --project PATH` | `PATH/.agents/skills/project-init` | 위 요구 사항과 기존 실제 프로젝트 디렉터리 |
| `--mode plugin` 또는 생략 | `~/plugins/codex-project-init` 및 개인 마켓플레이스 | Codex CLI와 번들 plugin-creator 도우미 |

두 로컬 모드 모두 `--dry-run`과 `--replace`를 지원합니다. `--project`는 스킬
전용이며 `--codex /absolute/path/to/codex`는 PATH가 다를 때 호환 CLI를 고르는
플러그인 전용 옵션입니다. 단독 스킬 설치는 미리 검증해 확보한 전체 파일을
복사하며 마켓플레이스를 등록하지 않습니다. GitHub에서 바로 설치할 때는
[Codex 스킬 설치 요청](../../README.md#단독-스킬)을 사용합니다. 디스크립터 API가
없는 플랫폼도 이 방식을 사용하며, 로컬 스킬 설치는 쓰기 전 사전 검사에서 종료됩니다.

### 빌드와 복구

패키징은 유지보수 대상 소스 경로를 선택하고 자격 증명용 파일 이름·캐시·관련
없는 루트 파일을 제외합니다. GitHub 목록은 명시적으로 배포에 포함하고,
다른 `.agents` 상태는 제외합니다. 목록의 플러그인 이름·루트 경로·정책을
검증합니다. 허용된 파일의 내용에서 시크릿을 탐지하지는
않습니다. 포함 대상의 심볼릭 링크와 특수 파일은 거부합니다.
ZIP 순서·시간·파일 권한을 정규화하므로 같은 Python·압축 도구에서 입력이
같으면 체크섬도 같습니다. 게시 전에 후보 파일을 검증하고, 처리 가능한 게시
오류가 발생하면 기존 배포 파일을 복원합니다.

로컬 플러그인 설치는 Codex의 스캐폴드·캐시 버전 갱신·`plugin add` 절차를 사용합니다.
dry run에서 소스·경로·도우미·CLI를 사전 확인하고 선택한 실행 파일과 설치
대상을 출력합니다. 소스 사본과 설치 대상은 서로 다른 경로여야 합니다.

플러그인 소스를 교체하기 전에 완전한 후보를 준비하고 검증합니다. 교체에 성공하면 설치
대상 옆에 시간 정보가 포함된 소스 백업을 남기고 정확한 경로를 결과에 표시합니다.
처리 가능한 교체 오류가 발생하면 이전 소스를 복원합니다.

첫 설치에서 마켓플레이스 등록 후 실패하면 등록 경로가 사라지지 않도록 완전한
소스를 유지합니다. 보고된 상태를 확인하고 `--dry-run --replace`로 재시도를
미리 검토합니다. Codex의 마켓플레이스·캐시 변경까지 복구했다고 주장하지
않습니다. 자동 소스 복원이 실패하면 보고된 복구 경로를 따르세요. 자식 프로세스
출력은 진단에서 숨기며 작업 이름과 종료 코드로 실패 단계를 구분합니다.

스킬 모드도 게시 전에 완전한 후보를 준비합니다. 교체하면 사용자 추가 파일을
포함한 이전 스킬 디렉터리 전체를 표시된 백업 경로에 보존합니다. 다른
프로세스가 대상을 바꾸거나 자동 복원이 실패하면 보고된 복구 경로를 확인합니다.
강제 종료를 복구 완료로 간주하지 않으며 재시도 전에 남은 설치·백업 디렉터리를
확인합니다. 의도한 설치 결과를 검증하기 전에는 백업을 삭제하지 않습니다.
상위 디렉터리가 이동했다면 진단에는 원래 경로가 표시됩니다. 수동 복구 전에
보존된 디렉터리의 현재 위치를 확인합니다.

공개·태그·푸시·실제 설치 변경은 사용자가 정한 대상과 범위를 따릅니다. 일반
소스 검증은 설치를 수행하지 않습니다. 스킬 작업 흐름을 변경하기 전에는
[동작 시나리오](../reference/skill-evaluation.md)를 실행합니다.
