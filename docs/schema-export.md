# 스키마 메타데이터 내보내기

**한국어** | [English](schema-export.en.md) · [문서 목차](README.md)

`cubrid-schema export`는 사용자가 선택한 CSQL 접속으로 보이는 카탈로그 메타데이터를 읽습니다.
기존 스키마 로더와 완성 인터페이스에서 사용할 버전 1 JSON 스냅샷 하나를 출력합니다.
코어 설치에 포함되며 선택 Python 의존성은 필요하지 않습니다.
POSIX 프로세스 그룹, 설치된 CSQL 클라이언트, 호출자가 설정한 CUBRID 환경이 필요합니다.

## 스냅샷 내보내기

신뢰하는 CSQL 실행 파일과 클라이언트/서버 DB 접속 대상을 지정합니다.

```sh
cubrid-schema export --csql /trusted/cubrid/bin/csql --timeout 5 -- -udba demodb@localhost -C > schema.json
```

종료 상태가 0이고 stdout에 완전한 유효 JSON이 있을 때만 스냅샷을 사용합니다.
요청, 수집, 파싱, 직렬화가 실패하면 stdout은 비어 있습니다.
출력이 시작된 후 파이프가 닫히거나 시간 초과 또는 취소가 발생하면 stdout에 일부 JSON이 남을 수 있으며 종료 상태는 0이 아닙니다.
이 파일을 기존 `schemaSnapshot` 설정으로 지정합니다. 마지막 정상 스냅샷을 교체할 때는 새 임시 파일로 먼저 내보냅니다.
접속 선택·암호 입력·캐시·새로고침 일정은 호출자나 편집기가 소유합니다.
`cubrid.reloadSchema`는 파일을 다시 읽습니다. CSQL에 접속하거나 새 메타데이터를 수집하지 않습니다.
완성·린트·검증·언어 서버 시작은 내보내기를 자동 실행하지 않습니다.

편집기나 다른 프로세스에서는 UTF-8 JSON 객체 하나를 stdin으로 보내고 stdin을 닫습니다.

```text
argv: ["cubrid-schema", "export", "--csql", "/trusted/cubrid/bin/csql", "--timeout", "5", "--request-stdin"]
stdin: {"requestVersion":1,"command":"csql -udba demodb@localhost -C","password":null}
```

JSON은 메모리에서 구성합니다. 암호를 셸 기록이나 exporter 인자에 넣지 않습니다.
`password`는 선택 필드입니다. null이면 명령 안의 암호를 유지하고, 없으면 빈 암호를 사용합니다.
문자열이면 명령 안의 암호를 덮어씁니다. 빈 문자열도 명시적인 덮어쓰기입니다.
CSQL의 배치 인증에는 실제 `-p` 인자가 필요하므로 CSQL 자식 프로세스의 인자에서 암호가 일시적으로 보일 수 있습니다.
가상의 암호 환경 변수를 사용하거나 암호를 SQL로 보내지 않습니다.

## 허용하는 요청

| 입력 | 의미 |
| --- | --- |
| `--csql PATH` | 신뢰하는 실행 파일. 기본값은 PATH의 `csql`입니다. 요청 안의 프로그램 이름은 실행 파일을 선택하지 않습니다. |
| `--timeout SECONDS` | 양의 유한 시간 제한. 기본 5초, 최대 300초이며 stdin 읽기, 결과 인코딩, stdout 출력을 포함합니다. |
| `--request-stdin` | JSON 요청을 읽습니다. `--` 뒤 접속 인자와 함께 사용할 수 없습니다. |
| `requestVersion` | 필수 정수 1. |
| `command` | 필수 비어 있지 않은 문자열. 확장 없이 `shlex` 따옴표 규칙으로 토큰화합니다. |
| `password` | 선택 문자열 또는 null. |

`--` 뒤 직접 인자와 JSON 명령은 같은 접속 파서를 사용합니다.
선두의 `csql` 또는 파일명이 `csql`인 경로는 설명용입니다.
사용자 옵션은 `-uNAME`, `-u NAME`, `--user=NAME`, `--user NAME`을 지원합니다. `-p`·`--password`도 같은 형식을 지원합니다.
같은 값의 중복은 허용하고 충돌하는 중복은 거부합니다.
`-C`·`--CS-mode`는 클라이언트/서버 모드이며 생략해도 이 모드를 사용합니다.
사용자를 생략하면 CSQL의 기본 사용자를 사용합니다.
`-`로 시작하는 암호에는 붙여 쓰기 또는 `=` 형식을 사용합니다.

DB 접속 대상은 정확히 하나여야 합니다. DB·호스트 이름에는 유니코드 단어 문자·점·하이픈을 허용합니다.
`@host`, 숫자 포트, 대괄호로 감싼 IPv6 호스트를 포함할 수 있습니다. `-`로 시작하거나 공백·셸 연산자를 포함할 수 없습니다.
독립 실행·관리자 모드, 임의 SQL, 입출력 파일, 모르는 옵션, 추가 피연산자는 자식 실행 전에 거부합니다.
셸은 실행하지 않습니다. 프로젝트 설정으로 CSQL 실행 파일이나 접속 자격 증명을 선택할 수 없습니다.

요청은 최대 64 KiB입니다. 모르는 JSON 키·중복 키·잘못된 타입·잘못된 UTF-8·따옴표 오류·NUL·JSON 뒤 추가 데이터를 거부합니다.
CSQL의 stdout과 stderr 합계는 최대 16 MiB이며 인코딩한 스냅샷 JSON도 별도로 최대 16 MiB입니다.
CSQL의 stderr 출력, 0이 아닌 종료 상태, 식별 행 누락, 일관성 없는 행, 잘못된 이스케이프, 소속 테이블이 없는 컬럼·인덱스는 실패입니다.
CSQL이 출력하는 마지막 빈 줄은 허용합니다. 그 외 예상하지 못한 출력은 거부합니다.
식별 행만 있으면 보이는 카탈로그가 비어 있는 정상 결과입니다. 권한·쿼리 오류는 실패입니다.

| 종료 상태 | 의미 |
| --- | --- |
| 0 | stdout에 완성된 스냅샷. |
| 2 | 잘못된 요청 또는 옵션. |
| 3 | CSQL 사용 불가·수집 실패·잘못된 카탈로그·출력 한도 초과·미지원 플랫폼. |
| 124 | 시간 제한 초과. |
| 130 | SIGTERM·SIGINT 또는 import API를 통한 취소. |

실패 시 비밀을 제거한 고정 메시지를 stderr에 출력하려고 시도합니다. stderr가 가득 찼거나 닫혔다면 메시지를 출력하지 못할 수 있습니다.
자식 stderr·예외 인자·원본 명령·암호는 전달하지 않습니다.
CSQL은 비공개 임시 작업 디렉터리에서 실행하여 `cub.err`를 격리하고 정상 정리 시 디렉터리를 삭제합니다.
성공·실패·시간 초과·처리 가능한 취소에서 소유한 프로세스 그룹을 종료하고 직접 자식을 회수합니다. 직접 자식이 먼저 끝나도 같습니다.
SIGKILL에서는 정리 핸들러가 실행되지 않습니다. 의도적으로 새 세션을 만드는 후손은 프로세스 그룹으로 격리할 수 없습니다.
실행 대상으로 신뢰하는 CSQL 클라이언트를 사용하며 불신 프로그램의 샌드박스를 제공하지 않습니다.

## 스냅샷 내용

스냅샷에는 `schemaVersion`, 인증된 `user`, 호스트를 제외한 DB 이름, `relations`, `users`가 있습니다.
관계마다 소유자·이름·CLASS/VCLASS 종류·컬럼·시스템 여부·인덱스를 보존합니다.
이름의 유니코드 표기와 디코딩한 탭·개행·백슬래시를 보존합니다.
메타데이터 전용 `source` 객체는 `endpoint` 필드만 포함합니다.
제한된 사용자의 성공 결과는 그 사용자에게 보이는 메타데이터이며 DB 전체 객체를 의미하지 않습니다.
기존 로더의 동작은 [스키마 계약](contracts.md#schema-snapshot)을 참고합니다.

## 어댑터 import

```python
from threading import Event
from cubrid_language.acquisition import acquire_schema, parse_connection, snapshot_json

cancelled = Event()
connection = parse_connection("csql -udba demodb@localhost -C", password=None)
schema = acquire_schema(connection, executable="/trusted/cubrid/bin/csql", timeout=5, cancelled=cancelled)
encoded = snapshot_json(schema, source=connection)
```

`Connection`은 불변 값이며 필드를 검증하고 repr에서 접속 정보를 숨깁니다.
`parse_connection`은 명령 문자열 또는 토큰화한 인자의 list/tuple을 받습니다.
`acquire_schema`는 기존 불변 `Schema`를 반환합니다. 실패 시 고정 `code`와 비밀 제거 메시지를 가진 `AcquisitionError`를 발생시킵니다.
선택 `threading.Event`를 설정하면 수집을 취소하고 소유한 그룹을 정리합니다.
`snapshot_json`도 양의 제한된 `timeout`과 선택 취소 이벤트를 받습니다.
언어 코어는 이 어댑터를 import하거나 메타데이터를 자동 수집하지 않습니다.

[검증 보고서](tickets/reports/schema-export.md)는 제어된 자식 프로세스 테스트와 별도 CUBRID 11.5 카탈로그 검사를 기록합니다.
이 수집 검증은 정확한 네이티브 파서 프로파일이나 그 검증 범위를 변경하지 않습니다.
