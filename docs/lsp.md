# stdio 언어 서버

**한국어** | [English](lsp.en.md)

선택 설치하는 Python 서버가 공통 CUBRID 완성과 오프라인 문법 진단을 LSP 3.17로 제공합니다.
편집기는 `cubrid-language-server` 자식 프로세스를 시작하고 표준 입력·출력으로 통신합니다.
인자 없이 서버를 시작합니다. TCP·WebSocket 수신 포트나 공유 daemon은 사용하지 않습니다.

## 설치와 실행

Python 3.10 이상에서 선택 의존성을 설치합니다.

```sh
uv venv --python 3.10 .venv
uv pip install --python .venv/bin/python '.[lsp]'
```

로컬 checkout에서 실행합니다. wheel 설치는 `.[lsp]` 대신 wheel 경로 뒤에 `[lsp]`를 붙입니다.
[설치·릴리스 검증](install.md)과 [V3 지원 범위](coverage.md)를 확인합니다.
편집기에 실행 명령 `cubrid-language-server`, 빈 인자 목록, stdio 전송을 지정합니다.
문서를 열 때 정확한 언어 ID `cubrid`를 사용합니다.
일반 `sql` 문서에는 완성·진단을 제공하지 않습니다.
[VS Code 확장](https://github.com/vimkim/cubrid-vscode)과 [Neovim 플러그인](https://github.com/vimkim/cubrid.nvim)은 공개 알파입니다. 각 저장소에서 설치와 설정을 확인합니다.
편집기 패키지는 Python 서버와 네이티브 런타임을 포함하거나 자동 다운로드하지 않습니다. 키워드 완성에는 서버가 필요하지만 네이티브 파서는 필요하지 않습니다. 엄격한 오프라인 문법 진단에는 검증된 워커, 일치하는 런타임과 정확한 프로파일이 필요합니다.

코어와 `cubrid-lint`의 필수 Python 런타임 의존성은 0개입니다.
LSP extra는 pygls 2.1.1, lsprotocol 2025.0.0, attrs 25.4.0, cattrs 25.3.0, typing-extensions 4.15.0을 고정합니다.
Python 3.10에서는 exceptiongroup 1.3.1도 사용합니다.
선택 의존성이 없으면 인자 없이 설치된 서버를 시작할 때 stderr에 설치 안내를 출력하고 상태 3으로 종료합니다.

서버를 시작하지 않고 설치된 배포본의 버전을 확인하려면 `cubrid-language-server --version`을 실행합니다.
사용법은 `cubrid-language-server --help` 또는 `-h`로 확인합니다. 각 옵션은 단독으로 사용합니다.
이 옵션에는 선택 LSP 의존성과 네이티브 런타임이 필요하지 않습니다.
설치된 배포 메타데이터가 없는 소스 실행에서는 버전을 확인할 수 없습니다. 먼저 패키지를 설치합니다.

## 신뢰하는 편집기 설정

`initialize.initializationOptions`로 다음 객체를 보냅니다.

```json
{
  "cubrid": {
    "parserWorker": "/absolute/trusted/parser-worker",
    "runtimePrefix": "/absolute/qualified/runtime",
    "profile": "cubrid-11.5.0.2704-cc94778",
    "schemaSnapshot": "/absolute/metadata/catalog.json"
  }
}
```

`workspace/didChangeConfiguration`으로 설정을 교체할 수 있습니다.

```json
{"settings":{"cubrid":{"schemaSnapshot":null}}}
```

각 알림은 이전 편집기 설정 전체를 교체합니다.
필드가 없으면 프로젝트 설정이나 기본값을 상속합니다. `schemaSnapshot: null`은 캐시의 스키마도 명시적으로 지웁니다.

| 설정 | 의미 |
| --- | --- |
| `profile` | 프로젝트 메타데이터보다 우선하는 파서 프로파일 |
| `scriptMode` | 프로젝트 설정·파일명 기본값보다 우선하는 `sql` 또는 `csql` |
| `schemaSnapshot` | 선택 JSON 스냅샷 경로 또는 비활성화하는 `null` |
| `configPath` | 명시적으로 선택하는 프로젝트 JSON 설정 파일 |
| `parserWorker` | 신뢰하는 워커 실행 파일의 절대 경로 |
| `runtimePrefix` | 신뢰하는 일치 런타임의 절대 경로 |
| `workerManifest` | 선택 manifest 절대 경로. 기본값은 워커 옆 `manifest.json` |
| `workerTimeout` | 양수 검사 제한 시간. 단위는 초, 기본값 5, 최대 300 |

`parserWorker`와 `runtimePrefix`는 함께 설정합니다.
[네이티브 안내](../native/parser-worker/README.md)에 따라 워커를 별도로 빌드·검증합니다.
서버는 PATH에서 워커를 찾거나 런타임을 다운로드하지 않습니다. 프로젝트 파일이 실행 파일을 선택할 수도 없습니다.

파일 문서는 [CLI와 같은 설정 규칙](lint-cli.md)을 사용합니다.
가장 가까운 조상의 `.cubrid-language.json`에서 메타데이터를 읽습니다.
명시한 `configPath`가 그 파일보다 우선하고, 편집기 필드가 가장 우선합니다.
프로젝트 스냅샷 상대 경로는 해당 설정 파일 디렉터리를 기준으로 해석합니다.
편집기 상대 경로는 초기화의 루트 디렉터리, 루트가 없으면 프로세스 작업 디렉터리를 기준으로 해석합니다.
프로젝트 파일에는 `profile`, `scriptMode`, `schemaSnapshot`만 허용합니다.

파일명 기본 모드는 대소문자를 구분하지 않는 `.csql`이면 `csql`, 그 외에는 `sql`입니다.
제목 없는 문서는 편집기가 `scriptMode`를 명시하지 않으면 `sql`을 사용합니다.
설정을 바꾸면 이전 검사를 취소하고 열린 CUBRID 문서를 다시 검사합니다.
잘못된 설정은 `CUBRID-T1003` 진단과 프로토콜 로그로 표시합니다.

## 완성과 스키마 스냅샷

완성은 캐시한 스키마 메타데이터와 공통 순수 함수 `complete`를 사용합니다.
클라이언트가 인코딩 목록을 생략해도 모든 위치에 UTF-16을 사용합니다.
동기화 방식은 Full입니다. 변경 알림마다 원문 전체를 보냅니다.
범위를 지정한 변경은 거부하고 원문을 유지합니다.
잘못된 줄, UTF-16 surrogate 내부, CRLF 종결자 내부 위치는 오류 `-32602`로 거부합니다.
각 완성 후보에는 커서 뒤 접미사까지 토큰 전체를 교체하는 명시적 `textEdit`이 있습니다.

선택 스냅샷은 [버전 1 스키마 계약](contracts.md#schema-snapshot)을 따릅니다.
스냅샷이 없어도 키워드 완성을 사용할 수 있습니다.
설정된 스냅샷을 읽지 못하면 `window/logMessage`로 표시합니다.
완성 요청은 DB에 연결하거나 파일을 읽지 않고 캐시를 사용합니다.

설정과 스냅샷을 명시적으로 다시 읽으려면 `workspace/executeCommand`를 보냅니다.

```json
{"command":"cubrid.reloadSchema"}
```

결과는 열린 문서별 `uri`, `profile`, `scriptMode`, `schemaAvailable`, `stale`, `availability` 목록입니다.
새로 고침이 실패하면 마지막 정상 메타데이터를 유지하고 결과와 로그에 stale 상태를 표시합니다.
성공하면 stale 상태를 해제합니다. 명시적인 `null`은 메타데이터를 즉시 제거합니다.
파일 감시와 DB 카탈로그 수집은 하지 않습니다.

## 진단과 수명 관리

열기·전체 변경·설정 새로 고침 후 250ms를 기다렸다가 검사합니다.
공통 `Validator`와 소유 워커 정리는 프로토콜 이벤트 루프 밖에서 실행합니다.
네이티브 초기화·검사가 느리거나 실패해도 완성을 사용할 수 있습니다.
런타임 설정이 없으면 `CUBRID-T1001` 진단을 게시합니다.
네이티브 결과의 공통 코드·심각도·분류·범위 정밀도를 유지합니다.
진단 게시에는 문서 버전이 포함됩니다.

새 버전은 이전 검사를 취소합니다. 오래된 결과는 현재 진단을 덮어쓰지 못합니다.
CUBRID 문서를 닫으면 빈 진단을 게시하고 소유한 작업을 취소합니다.
취소는 실행 대기 중인 검사도 포함하여 소유 검증기를 닫습니다.
`shutdown`, `exit`, 입력 EOF는 소유 워커를 정리합니다.
정상 shutdown 후 exit는 상태 0, shutdown 없는 exit·EOF는 상태 1로 종료합니다.
취소된 요청은 프로토콜 취소 오류 `-32800`을 받습니다.
stdout에는 프레임 프로토콜 메시지만 출력합니다. 서버 오류는 stderr, 워커 stderr는 별도 캡처로 분리합니다.

## 헤드리스 검증

소스 체크아웃에서 다음을 실행합니다.

```sh
just test
just test-lsp
just test-native-parser
just test-lsp-native
just build
```

`test-lsp`는 명시적으로 신뢰한 테스트 자식 워커와 실제 stdio 프레임을 검사하며 선택 의존성이 필요합니다.
`test-lsp-native`는 이 체크아웃과 일치하게 빌드한 워커·manifest가 필요합니다.
필수 검증에서 전제 조건이 없으면 실패합니다. 기본 테스트는 pygls와 네이티브 산출물 없이 실행합니다.
선택·네이티브 LSP 테스트는 Python 3.10·3.14에서 통과합니다.
네이티브 문법 범위는 [검증된 범위](../native/parser-worker/QUERY_DML_AUDIT.md)를 따릅니다.
