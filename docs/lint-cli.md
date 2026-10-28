# 오프라인 린트 CLI와 검증 API

**한국어** | [English](lint-cli.en.md)

`cubrid-lint`는 공통 `Validator`로 파일과 표준 입력의 문법을 검사합니다.
입력 SQL·CSQL 명령·include·셸 구문을 실행하지 않습니다.
Python 3.10 이상이며 필수 Python 의존성은 없습니다.
엄격한 검사에는 별도로 빌드·검증한 네이티브 워커와 런타임이 필요합니다.
[네이티브 빌드·설치 안내](../native/parser-worker/README.md)를 참고하세요.

## 설치와 파일 검사

사용할 Python 환경에 패키지를 설치합니다.

```sh
uv pip install .
```

신뢰하는 워커와 런타임 경로를 명시합니다.

```sh
cubrid-lint \
  --parser-worker /absolute/trusted/parser-worker \
  --runtime-prefix /absolute/qualified/runtime \
  --format json first.sql second.csql -
```

`-`는 표준 입력을 바이트로 한 번만 읽으며 인자에 한 번만 쓸 수 있습니다.
파일도 바이트로 읽고 엄격한 UTF-8로 디코딩합니다.
유니코드·CRLF·공백과 입력 경로의 표기를 유지합니다.
8 MiB 초과 입력·잘못된 UTF-8·NUL·읽을 수 없는 파일은 도구 오류입니다.
실패한 입력도 입력 순서대로 문서 결과를 반환합니다.
디렉터리를 재귀 검색하거나 glob을 확장하지 않습니다. 디렉터리 입력은 오류입니다.

옵션은 `--profile ID`, `--script-mode sql|csql`, `--format human|json`,
`--config PATH`, `--parser-worker PATH`, `--runtime-prefix PATH`입니다.
기본 출력은 `human`입니다. 워커와 런타임 경로는 함께 지정해야 합니다.
명시한 상대 경로는 작업 디렉터리를 기준으로 해석합니다.
manifest 기본 경로는 워커 옆의 `manifest.json`입니다.
프로젝트 설정·환경 변수로 워커나 런타임을 선택할 수 없습니다.
PATH 검색·런타임 다운로드·DB 버전 조회를 하지 않습니다.
워커 설정이 없으면 빈 파일도 명시적으로 실패합니다.

## 출력과 종료 코드

사람용 진단 형식은 `path:line:column: severity code message`입니다.
행과 유니코드 코드 포인트 열은 1부터 시작하며 파일별 상태 줄도 출력합니다.
문장 범위는 앞의 공백이나 주석을 포함할 수 있어 첫 SQL 토큰보다 앞을 가리킬 수 있습니다.

JSON stdout은 `schemaVersion: 1`, `offsetEncoding: unicode-codepoints`,
입력 순서의 `documents`, 전체 `status`를 가진 객체 하나입니다.
문서에는 `path`, `profile`, `scriptMode`, `status`, `coverage`, `diagnostics`, `statementKinds`가 있습니다.
각 진단은 `code`, `severity`, `message`, `category`, `rangePrecision`, `span`을 가집니다.
`span.start`와 `span.end`는 원문 코드 포인트 오프셋이며 끝 위치는 범위에서 제외합니다.
CR과 LF는 각각 하나로 셉니다. 네이티브 진단은 현재 문장 단위 정밀도입니다.
로그와 인자 오류 안내는 JSON stdout에 섞이지 않습니다.
잘못된 인자는 문서를 읽기 전에 stderr 안내와 종료 코드 3을 반환합니다.

| 코드 | 의미 |
| --- | --- |
| 0 | 모든 문서를 지원 범위 안에서 검사했으며 정상 |
| 1 | 도구 오류 없이 문법 오류 존재 |
| 2 | 도구·문법 오류 없이 미지원 구문 존재 |
| 3 | 도구·입력·설정·명령행 인자 오류 |

우선순위는 도구 오류 → 문법 오류 → 미지원 → 정상입니다.
미지원 경고도 성공 종료를 막습니다. `--ignore-unsupported` 옵션은 없습니다.
마지막 세미콜론이 없는 EOF는 선택한 네이티브 파서가 허용하면 통과합니다.

## 공통 프로젝트 설정

선택 사항인 `.cubrid-language.json`에는 메타데이터만 둡니다.

```json
{
  "profile": "cubrid-11.5.0.2704-cc94778",
  "scriptMode": "sql",
  "schemaSnapshot": "metadata/schema.json"
}
```

| 키 | 허용 값 |
| --- | --- |
| `profile` | 비어 있지 않은 유니코드 프로파일 식별자 |
| `scriptMode` | `sql` 또는 `csql` |
| `schemaSnapshot` | 비어 있지 않은 유니코드 경로 또는 메타데이터를 끄는 `null` |

모든 키는 생략할 수 있습니다. 알 수 없는 키와 중복 키는 거부합니다.
실행 파일·런타임·명령·인증 정보 설정은 허용하지 않습니다.
잘못된 JSON·유니코드·자료형이나 읽을 수 없는 설정은 `CUBRID-T1003`입니다.
모르는 프로파일도 그대로 선택하며 설정된 워커에서 `CUBRID-U1001`로 실패합니다.

필드별 우선순위는 다음과 같습니다.

1. 명시한 플래그 또는 호출자 설정.
2. `--config` 또는 `config_path`로 지정한 파일.
3. 가장 가까운 상위 `.cubrid-language.json`.
4. 기본값.

입력 파일마다 지정한 경로의 부모 디렉터리에서 탐색합니다.
표준 입력과 이름 없는 편집 문서는 작업 디렉터리에서 시작합니다.
가장 가까운 설정 하나만 사용하며 빠진 필드를 더 먼 상위 파일에서 찾지 않습니다.
상위 값으로 덮어쓰더라도 참여하는 설정 파일은 모두 유효해야 합니다.
각 설정의 상대 스냅샷 경로는 해당 설정 파일의 디렉터리를 기준으로 해석합니다.
호출자가 넘긴 상대 스냅샷 경로는 작업 디렉터리를 기준으로 합니다.
`~`나 환경 변수는 확장하지 않습니다.

기본 프로파일은 `cubrid-11.5.0.2704-cc94778`입니다.
확장자 대소문자와 관계없이 `.csql`은 `csql` 모드이며 다른 파일과 표준 입력은 `sql`입니다.
`schemaSnapshot`은 오프라인 완성용 메타데이터이며 린터의 의미 검사를 켜지 않습니다.

## Python 인터페이스

호출자는 신뢰하는 워커 설정을 주입하고 컨텍스트 관리자 또는 `close()`로 종료합니다.

```python
from pathlib import Path
from cubrid_language.validation import PROFILE, Validator, WorkerConfig

config = WorkerConfig(
    executable=Path('/absolute/trusted/parser-worker'),
    runtime_prefix=Path('/absolute/qualified/runtime'),
)
with Validator(config) as validator:
    result = validator.validate("SELECT '가😀';", PROFILE, 'sql')
    print(result.status, result.to_dict())
```

`validate(text, profile, script_mode)`는 원본 유니코드 문서 문자열만 받습니다.
잘못된 입력·프로파일·모드·설정은 `CUBRID-T1003`, 설정 부재는 `CUBRID-T1001`입니다.
종료 후 호출은 `CUBRID-T1002`이며 반복 종료는 안전합니다.
다른 스레드의 `close()`는 진행 중 검증을 중단하고 이후 워커 생성을 막습니다.
취소·종료 후에는 새 검증기를 만듭니다. 프로파일이 바뀌면 기존 워커를 종료합니다.
라이브러리가 문법·지원 범위를 판단하며 서로 다른 진단과 원문 순서·상태 우선순위를 유지합니다.

CLI나 편집기 설정에서 같은 해석 함수를 사용할 수 있습니다.

```python
from cubrid_language.config import resolve_config
from cubrid_language.schema import load_snapshot

settings = resolve_config('query.sql', config_path='settings.json', script_mode='sql')
snapshot = load_snapshot(settings.schema_snapshot)
# snapshot.schema를 완성에 전달하고 snapshot.availability를 표시합니다.
settings = resolve_config('query.sql', schema_snapshot=None)
assert settings.schema_snapshot is None
```

반환형은 불변 `ResolvedConfig(profile, script_mode, schema_snapshot)`입니다.
`schema_snapshot`을 생략하면 상속하며 명시한 `None`은 메타데이터를 끕니다.
프로젝트의 `schemaSnapshot: null`도 낮은 우선순위의 스냅샷을 끕니다.
`ConfigError.code`는 `CUBRID-T1003`입니다. 신뢰하는 워커 설정은 별도로 전달합니다.

## 현재 검증 범위

현재 Python 단계는 위에서 지정한 Linux x86-64 CUBRID 11.5 프로파일만 검증합니다.
워커는 검증한 리터럴 SELECT와 CREATE SERIAL 형식을 지원합니다.
query·DML 확대와 전체 혼합 스크립트 분류는 별도 티켓입니다.
두 모드 모두 현재 워커의 보수적인 지원 범위를 사용합니다.
검증하지 않은 프로시저·include·셸 구문은 명시적인 미지원 결과를 반환합니다.
문법 통과는 객체 존재·권한·서버 의미 검증을 뜻하지 않습니다.
