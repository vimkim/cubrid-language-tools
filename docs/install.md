# 개발 버전 설치와 검증

**한국어** | [English](install.en.md) · [문서 목차](README.md)

Python 3.10 이상을 사용합니다. 이 로컬 개발 버전은 `0.1.0.dev0`입니다.
아래 명령은 로컬 checkout 또는 빌드 산출물을 설치하며 패키지 인덱스 게시를 가정하지 않습니다.
문법 통과를 해석하기 전에 [검증된 지원 범위](coverage.md)를 확인합니다.

## PATH에 CLI·LSP 설치

uv와 just를 준비한 뒤 checkout에서 실행합니다.

```sh
just sync
cubrid-lint --help
cubrid-language-server --version
```

`just install`은 `just sync`의 별칭입니다.
두 명령은 `uv tool install --reinstall '.[lsp]'`로 CLI·LSP와 고정된 선택 의존성을 uv 도구 환경에 설치합니다.
다시 실행하면 현재 checkout으로 재설치합니다.
셸에서 명령을 찾지 못하면 `uv tool update-shell`을 실행한 뒤 셸을 다시 시작합니다.
편집기가 PATH의 `cubrid-language-server`를 인자 없이 stdio 자식 프로세스로 실행하도록 설정합니다.
완성은 바로 사용할 수 있습니다. 엄격한 진단에는 아래의 네이티브 워커·런타임을 별도로 준비합니다.

## 코어·CLI 설치

공개 저장소를 복제하고 전용 환경에 설치합니다.

```sh
git clone https://github.com/vimkim/cubrid-language-tools.git
cd cubrid-language-tools
```

```sh
uv venv --python 3.10 .venv
uv pip install --python .venv/bin/python .
.venv/bin/cubrid-lint --help
.venv/bin/python -I -c "from cubrid_language import complete; print(complete('sel', 3, 'cubrid-11.5.0.2704-cc94778'))"
```

코어·CLI의 필수 Python 런타임 의존성은 0개입니다.
완성은 바로 사용할 수 있으며 엄격한 린트에는 아래의 신뢰된 네이티브 입력도 필요합니다.
두 console 명령을 모두 설치합니다. `cubrid-language-server --version`은 선택 의존성이나 네이티브 런타임 없이 설치된 배포본의 버전을 출력합니다.
선택 의존성이 없으면 인자 없이 서버를 시작할 때 stderr에 안내를 출력하고 상태 3으로 종료합니다.
설치된 배포 메타데이터가 없는 소스 실행에서는 버전을 확인할 수 없습니다. 먼저 패키지를 설치합니다.

산출물을 설치하려면 빌드한 뒤 다음 입력을 사용합니다.

```sh
uv build
uv pip install --python .venv/bin/python dist/cubrid_language_tools-0.1.0.dev0-py3-none-any.whl
```

소스 배포본 `dist/cubrid_language_tools-0.1.0.dev0.tar.gz`도 설치할 수 있습니다.
격리 빌드는 setuptools 77.0.3 이상이 필요합니다. 빌드 의존성은 런타임 의존성과 별개입니다.
[릴리스 검증 recipe](#로컬-릴리스-검증)는 정확한 최소 backend를 검사합니다.

## 선택적 stdio 서버 설치

checkout에서 호출자 환경에 고정된 선택 의존성을 설치합니다.

```sh
uv pip install --python .venv/bin/python '.[lsp]'
```

로컬 wheel은 `'dist/cubrid_language_tools-0.1.0.dev0-py3-none-any.whl[lsp]'`을 사용합니다.
선택 의존성은 pygls 2.1.1·lsprotocol 2025.0.0·attrs 25.4.0·cattrs 25.3.0·typing-extensions 4.15.0으로 고정합니다.
Python 3.10에서는 exceptiongroup 1.3.1도 사용합니다.
편집기가 `.venv/bin/cubrid-language-server`를 인자 없이 stdio 자식 프로세스로 실행하도록 설정합니다.
문서는 `cubrid` 언어 ID로 엽니다. [LSP 설정 안내](lsp.md)를 참조합니다.
[VS Code 확장](https://github.com/vimkim/cubrid-vscode)과 [Neovim 플러그인](https://github.com/vimkim/cubrid.nvim)의 설치 안내를 확인합니다.
두 패키지에 Python 서버와 네이티브 런타임은 포함되지 않으며 자동으로 다운로드하지 않습니다. 키워드 완성에는 서버가 필요하지만 네이티브 파서는 필요하지 않습니다.

## 검증된 네이티브 워커 준비

엄격한 검사에는 Linux x86-64와 정확한 CUBRID 개발 프로파일 `cubrid-11.5.0.2704-cc94778`이 필요합니다.
고정 소스·일치하는 생성 헤더·라이브러리·런타임 파일을 준비합니다.
C++17 컴파일러·OpenSSL 개발 헤더·libcrypto가 필요하며 trace 검증에는 strace도 필요합니다.
[네이티브 빌드 안내](../native/parser-worker/README.md#reproduce-this-host-qualification)의 명시적 네 입력으로 워커를 빌드합니다.
고정 커밋의 헤더를 현재 소스 헤더로 대체하거나 인접 버전 라이브러리를 선택하지 않습니다.

production 워커·내장 digest에 연결된 `manifest.json`·빌드 근거·notice를 신뢰된 디렉터리에 함께 보관합니다.
정확한 런타임 파일을 검증된 manifest 경로에 유지합니다.
입력을 이동하면 재빌드·재검증이 필요하며 manifest를 편집하면 digest가 무효화됩니다.
Python wheel에는 워커·런타임이 없습니다. 소스 배포본에는 워커 소스·빌드 도구·감사·fixture·notice가 있습니다.
런타임을 자동 다운로드하지 않습니다.

명시적인 신뢰 경로로 독립 표준 입력 예시를 실행합니다.

```sh
printf 'SELECT 1;\n' | .venv/bin/cubrid-lint \
  --parser-worker /absolute/trusted/parser-worker \
  --runtime-prefix /absolute/qualified/runtime \
  --format json -
```

검증된 프로파일에서는 상태 `valid`·검사 범위 `complete`·종료 코드 0을 반환합니다.
`DESCRIBE absent;`는 `unsupported`·검사 범위 `none`·코드 `CUBRID-U1002`·종료 코드 2를 반환합니다.
직접 라이브러리 검증에는 [공통 Validator 예시](lint-cli.md)를 사용합니다.
워커·런타임 경로는 명시적 CLI 옵션이나 신뢰된 사용자·편집기 설정에서만 받습니다.
프로젝트 `.cubrid-language.json`에는 프로파일·스크립트 모드·스냅샷 메타데이터만 넣을 수 있습니다.

편집기와 CLI는 소유한 자식 프로세스를 생성하고 pipe를 사용합니다.
TCP 수신 포트·DB 접속·SQL 실행·공유 daemon은 필요하지 않습니다.
네이티브 manifest는 소스·헤더·라이브러리 및 런타임 해시·설정·플랫폼·V3 범위 리비전을 결합합니다.
입력이 없거나 일치하지 않으면 빈 문서도 명시적 실패 결과를 반환합니다.
기본 제한은 요청 5초·입력 8 MiB·응답 16 MiB·진단 256개입니다.
비정상 종료 시 워커의 전용 임시 디렉터리가 남을 수 있습니다. 정상 종료는 자신의 디렉터리를 제거합니다.

## 로컬 릴리스 검증

uv와 Python 3.10·3.14를 준비합니다. 먼저 정확한 네이티브 입력으로 V3 워커를 빌드합니다.
명령·로그·환경·산출물을 보존할 새 출력 디렉터리를 사용합니다.

```sh
just test
just test-native-parser
just test-lsp
just test-lsp-native
just qualify-release native/parser-worker/build /absolute/new/release-evidence
```

recipe는 두 Python 버전의 격리 wheel·소스 빌드에 setuptools 77.0.3을 강제합니다.
코어·선택 의존성 산출물을 checkout 밖의 독립 환경 8개에 설치합니다.
archive 검사는 소스·notice 바이트, 두 console 진입점, 선택 의존성 6개, 네이티브 컴파일 결과물 제외를 확인합니다.
이식 가능한 fixture로 설치된 라이브러리·CLI의 상태·검사 범위·코드·원문 범위를 비교합니다.
선택 의존성 설치에서는 완성 후보 순서·편집 범위와 한글·이모지·CRLF의 명시적 UTF-16 진단 기대값도 비교합니다.
LSP는 상태·검사 범위의 진단 결과를 전달하며 별도 상태·범위 프로토콜 필드를 추가하지 않습니다.
코어 환경에서는 기본 suite·선택 의존성 부재 명령을, 선택 환경에서는 framed suite·의존성 버전을 검사합니다.
네이티브·선택 의존성이 없으면 필수 검사는 명시적으로 실패하며 skip으로 통과하지 않습니다.
이 recipe는 소스·런타임·DB·daemon·원격 저장소를 변경하지 않습니다.

## 라이선스·notice 보존

프로젝트 코드는 [Apache License 2.0](../LICENSE)을 사용합니다.
SPDX 메타데이터는 `license = "Apache-2.0"`과 명시적 license 파일 목록을 사용합니다.
변경은 [setuptools 안내](https://setuptools.pypa.io/en/stable/userguide/license_migration.html)와
[Python 패키징 안내](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)를 따릅니다.
두 archive는 프로젝트 라이선스·네이티브 구성 요소 원문 17개·목록을 보존합니다.
wheel은 배포 메타데이터의 `licenses` 디렉터리에 이 파일을 보관합니다.

[네이티브 notice 목록](../native/parser-worker/notices/README.md)은 별도 공급하는 CUBRID·헤더·시스템 의존성을 기록합니다.
메타데이터가 재배포 런타임 번들의 법적 검토 완료를 뜻하지 않습니다.
네이티브 산출물 전달 시 원래 저작권 표시와 실제 구성 요소 조건을 보존합니다.
