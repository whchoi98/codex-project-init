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
python3 scripts/install.py --dry-run
```

3. Verify `dist/manifest.json` checksums and both ZIP contents. The validation
   command checks metadata, selected payload, and agreement with current source.
   The plugin archive contains this source package; the standalone archive
   contains the entire `project-init` folder, including its sibling Python
   implementation package, references, and assets. Rebuild after the last edit.
4. Install with `python3 scripts/install.py`; use `--replace` for an intentional
   update after reviewing its dry run. The source backup path is printed.
   Use `--codex /absolute/path/to/codex` when the privileged environment has a
   different PATH or an older system Codex cannot read the current configuration.
5. Open a new Codex thread and verify that Project Init is discoverable.

### Build and recovery

Packaging selects maintained source roots and excludes credential-oriented
filenames, caches, and unrelated root files. It does not scan allowed file
contents for secrets. Included symlinks and special files are
rejected. ZIP order, timestamps, and file modes are normalized; unchanged inputs
produce the same checksums with the same Python/compression tooling. The builder
validates a candidate before publication and restores existing artifacts if a
handled publication failure occurs.

The installer uses Codex's scaffold, cachebuster, and `plugin add` flow. Its dry
run performs source/path/helper/CLI preflight and prints the selected executable
and destination. It requires the source checkout to be separate from the
installation destination.

Before replacing a source, the installer prepares and validates a complete
candidate. Successful replacements leave a timestamped source backup beside
the destination, with the exact path printed in the result. On a handled
replacement failure, the previous source is restored.

If a first installation fails after publishing a marketplace entry, a complete
source is retained so the entry does not point at a missing directory. Review
the reported state and preview a retry with `--dry-run --replace`. The installer
does not claim to roll back Codex's marketplace/cache effects. Follow any
reported recovery path if automatic source restoration fails. Child output is
withheld from diagnostics; the operation and exit status identify the failed step.

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
python3 scripts/install.py --dry-run
```

3. `dist/manifest.json`의 체크섬과 두 ZIP 내용을 확인합니다. 검증 명령은
   메타데이터·배포 대상·현재 소스와의 일치 여부를 확인합니다. 플러그인 ZIP은
   이 소스 패키지를 포함하고, 단독 스킬 ZIP은 Python 구현 패키지·참조 문서·
   템플릿을 포함한 `project-init` 폴더 전체를 담습니다. 마지막 편집 후 다시
   빌드합니다.
4. `python3 scripts/install.py`로 설치합니다. 의도한 갱신은 dry run 확인 후
   `--replace`를 사용합니다. 이전 소스의 백업 경로가 출력됩니다.
   권한 환경의 PATH가 다르거나 구버전 시스템 Codex가 현재 설정을 읽지 못하면
   `--codex /absolute/path/to/codex`로 실행 파일을 명시합니다.
5. 새 Codex 대화에서 Project Init 스킬이 검색되는지 확인합니다.

### 빌드와 복구

패키징은 유지보수 대상 소스 경로를 선택하고 자격 증명용 파일 이름·캐시·관련
없는 루트 파일을 제외합니다. 허용된 파일의 내용에서 시크릿을 탐지하지는
않습니다. 포함 대상의 심볼릭 링크와 특수 파일은 거부합니다.
ZIP 순서·시간·파일 권한을 정규화하므로 같은 Python·압축 도구에서 입력이
같으면 체크섬도 같습니다. 게시 전에 후보 파일을 검증하고, 처리 가능한 게시
오류가 발생하면 기존 배포 파일을 복원합니다.

설치 도구는 Codex의 스캐폴드·캐시 버전 갱신·`plugin add` 절차를 사용합니다.
dry run에서 소스·경로·도우미·CLI를 사전 확인하고 선택한 실행 파일과 설치
대상을 출력합니다. 소스 사본과 설치 대상은 서로 다른 경로여야 합니다.

소스를 교체하기 전에 완전한 후보를 준비하고 검증합니다. 교체에 성공하면 설치
대상 옆에 시간 정보가 포함된 소스 백업을 남기고 정확한 경로를 결과에 표시합니다.
처리 가능한 교체 오류가 발생하면 이전 소스를 복원합니다.

첫 설치에서 마켓플레이스 등록 후 실패하면 등록 경로가 사라지지 않도록 완전한
소스를 유지합니다. 보고된 상태를 확인하고 `--dry-run --replace`로 재시도를
미리 검토합니다. Codex의 마켓플레이스·캐시 변경까지 복구했다고 주장하지
않습니다. 자동 소스 복원이 실패하면 보고된 복구 경로를 따르세요. 자식 프로세스
출력은 진단에서 숨기며 작업 이름과 종료 코드로 실패 단계를 구분합니다.

공개·태그·푸시·실제 설치 변경은 사용자가 정한 대상과 범위를 따릅니다. 일반
소스 검증은 설치를 수행하지 않습니다. 스킬 작업 흐름을 변경하기 전에는
[동작 시나리오](../reference/skill-evaluation.md)를 실행합니다.
