# 검증된 지원 범위

**한국어** | [English](coverage.en.md) · [문서 목차](README.md)

이 문서는 Python 개발 버전 `0.1.0.dev0`의 제한된 지원 범위를 설명합니다.
네이티브 프로파일은 Linux x86-64의 정확한 `cubrid-11.5.0.2704-cc94778` 빌드입니다.
소스 커밋은 `cc947788d3b7dc402f46192d0f3299ddcc8563ba`, 범위 리비전은 `bounded-query-dml-schema-engineer-v3`입니다.
다른 11.5 빌드를 포함한 다른 빌드는 별도 검증이 필요합니다.
Python wheel에는 네이티브 워커·CUBRID 라이브러리·런타임 파일이 포함되지 않습니다.

## 자동 완성

`complete`는 미완성 SQL·지원 세션 명령의 후보 순서와 대체 범위를 반환합니다.
선택적 오프라인 스냅샷으로 이름·소유자·컬럼·인덱스·사용자·DB 정보를 제공합니다.
완성 어휘는 csql-future에서 가져온 [11.4 매뉴얼 출처](completion-provenance.md)를 유지합니다.
명시적 프로파일 인자는 버전별 어휘를 전환하지 않습니다.
완성 후보가 엄격한 11.5 문법 지원이나 서버 의미를 보장하지 않습니다.
완성에는 네이티브 런타임이 필요 없고 I/O를 수행하지 않습니다.

## 엄격한 SQL 문법 검사

아래 예시는 파서 단계 검사를 통과합니다. 대상 객체가 실제로 존재할 필요는 없습니다.
기재된 기능만 검증 범위에 포함됩니다. 허용된 입력도 네이티브 트리·오류 상태·문법 설정 검사를 통과해야 합니다.
제외 기능은 네이티브 파싱 전에 미지원으로 판정합니다.
허용 기능 내 잘못된 문법은 문법 오류가 됩니다. 계열이 모호한 미완성 입력은 미지원일 수 있습니다.

| 계열 | 예시 | 검증 기능과 제한 |
| --- | --- | --- |
| SELECT | `SELECT a.id FROM absent a WHERE a.id >= 3;` | 이름·한정 이름·별표·별칭·DISTINCT·FROM·WHERE. ORDER·GROUP·HAVING·LIMIT·집합 연산·INTO·힌트 제외 |
| 조인 | `SELECT a.id FROM a LEFT JOIN b ON a.id=b.id;` | 쉼표·INNER·기본 JOIN·LEFT·RIGHT·CROSS·ON·테이블 괄호. NATURAL·FULL·USING 컬럼·DBLINK 제외 |
| 표현식 | `SELECT (1+2)*3, '가😀', NULL;` | 최대 38자리 정수·일반 문자열·이름·괄호·산술·비교·IS NULL·AND·OR·NOT·EXISTS. 함수·정수 외 수치·캐스트·IN·BETWEEN·LIKE·CASE·변수·시리얼 값 제외 |
| CTE·서브쿼리 | `WITH c AS (SELECT 1 AS n) SELECT n FROM c;` | 비재귀 중첩·복수 CTE, 스칼라·파생 쿼리, EXISTS·상관 이름. CTE·테이블 별칭 컬럼 목록 제외 |
| INSERT | `INSERT INTO absent (id) VALUES (1);` | VALUES 행·SELECT·CTE 입력. 컬럼 목록 앞 대상은 비한정 이름만 허용. SET·DEFAULT·REPLACE·중복 키 절 제외 |
| UPDATE | `UPDATE absent SET id=2 WHERE id=1;` | 테이블 참조·별칭·조인·제한된 대입·WHERE. 커서·OBJECT·ORDER·LIMIT·즉시 `SET (` 제외 |
| DELETE | `DELETE FROM absent WHERE id=1;` | 테이블 참조·별칭·WHERE·복수 대상 이름·조인. USING·커서 제외 |
| MERGE | `MERGE INTO a USING b ON a.id=b.id WHEN MATCHED THEN UPDATE SET a.id=b.id;` | MATCHED UPDATE·NOT MATCHED INSERT와 선택적 절별 WHERE. DELETE·기본값·힌트·원격 참조 제외 |
| CREATE TABLE | `CREATE TABLE absent (id INTEGER, n BIGINT);` | 단순 이름과 선택적 INT·INTEGER·SMALLINT·BIGINT 컬럼. 제약·기본값·타입 인자·객체 타입·옵션 제외 |
| ALTER TABLE | `ALTER TABLE absent ADD COLUMN n INTEGER;` | ADD·선택적 COLUMN과 그룹 없는 정수 컬럼. 다른 동작·복수 ALTER 절 제외 |
| VIEW | `CREATE VIEW v AS SELECT id FROM absent;` | 제한된 쿼리의 CREATE, `CHANGE QUERY`의 ALTER, DROP. OR REPLACE·컬럼 선언·CHECK OPTION·쿼리 번호 제외 |
| DROP TABLE·VIEW | `DROP TABLE absent, other;` | 명시적 TABLE·VIEW와 쉼표로 구분한 단순 이름. IF EXISTS·소유자 한정·ONLY·ALL·CASCADE 제외 |
| INDEX | `CREATE INDEX ix ON absent (id DESC);` | 단순 이름·컬럼·ASC·DESC. ALTER는 `ON absent REBUILD`, DROP은 `ON absent` 필요. UNIQUE·REVERSE·표현식·접두 길이·ONLINE·WHERE 제외 |
| SERIAL | `CREATE SERIAL s START WITH 1 INCREMENT BY 2;` | 기존 제한 정수 옵션·ALTER 옵션·이름이 있는 DROP. 소유자·한정·인용 시리얼 이름 제외. 정확한 제한은 원래 감사 문서 참조 |
| SHOW | `SHOW TRACE;` | 정확한 SHOW TRACE만 허용 |
| EVALUATE | `EVALUATE 1/0;` | 제한된 표현식·서브쿼리. INTO·함수 제외. 표현식은 실행하지 않음 |
| 통계 | `UPDATE STATISTICS ON absent, other;` | 명시적 이름만 허용. ALL·CATALOG CLASSES·옵션 제외 |
| 설정 | `SET SYSTEM PARAMETERS 'ansi_quotes=no';` | 일반 문자열 목록. 내용을 파라미터 값으로 검사하거나 적용하지 않음 |
| 추적 | `SET TRACE ON OUTPUT JSON;` | ON·OFF와 선택적 OUTPUT TEXT·JSON. 추적 상태를 변경하지 않음 |
| 트랜잭션 | `SAVEPOINT s; ROLLBACK TO SAVEPOINT s; COMMIT WORK;` | COMMIT의 선택적 WORK·RETAIN LOCK, ROLLBACK의 선택적 WORK·TO SAVEPOINT, 이름·문자열 SAVEPOINT. 트랜잭션 실행 없음 |

단순 인용 식별자는 내부 구분자·이스케이프·점·제어 문자를 제외합니다.
함수·일반 SHOW·준비된 SQL·PL/CSQL·호스트 및 세션 변수와 기재되지 않은 구문은 미지원입니다.
정확한 predicate 조건은 [쿼리·DML 감사](../native/parser-worker/QUERY_DML_AUDIT.md),
[스키마·엔지니어 감사](../native/parser-worker/SCHEMA_ENGINEER_AUDIT.md), [원래 감사](../native/parser-worker/AUDIT.md)에 있습니다.
[네이티브 코퍼스](../native/parser-worker/qualification/corpus.json)는 정상 99건·문법 오류 80건·미지원 146건, 총 325건입니다.
미실행 trace 근거는 해당 코퍼스에 한정됩니다. 프로세스 분리는 운영체제 sandbox가 아닙니다.

## 수용된 네 가지 제외 항목

`SHOW COLUMNS FROM absent;`, `DESCRIBE absent;`, `DESC absent;`, 클래스 설명용 `EXPLAIN absent;`는 미지원입니다.
사용자는 2026-10-29에 첫 프로파일의 이 제한을 수용했습니다.
고정 클라이언트 helper는 접속 상태가 필요하며 미접속 상태에서 네이티브 오류 -224를 반환합니다.
원래 객체 설명 검증 기준은 통과하지 않았습니다.
별도 검증한 parser-only backend는 [후속 과제](roadmap.md#language-depth)입니다.
`EXPLAIN SELECT`도 미지원입니다. 이 릴리스의 EXPLAIN production은 클래스를 설명합니다.

## CSQL batch 문서

CSQL 모드는 첫 컬럼의 전체 명령 `;help`, `;exit`, `;commit`, `;rollback`, `;autocommit on/off`, `;time on/off`, `;line-output on/off`도 대소문자 구분 없이 허용합니다.
명령과 필수 인자 사이나 명령 뒤에는 ASCII 공백·탭을 허용합니다.
검사기는 `;exit` 뒤도 검사하며 세션이나 트랜잭션 상태를 변경하지 않습니다. commit·rollback은 텍스트 형식만 검사합니다.
들여쓰기·축약·include·셸 명령·버퍼 제어·프로시저 본문은 미지원입니다.
명령으로 중단된 미완성 SQL과 절차 영역은 EOF까지 미지원으로 유지합니다.
[batch 참조](scripts.md)에 lexical 보호와 원문 범위가 정의되어 있습니다.

## 결과와 위치

라이브러리·CLI 상태는 `valid`, `syntax-error`, `unsupported`, `tool-error`입니다.
상태 우선순위는 `tool-error > syntax-error > unsupported > valid`입니다.
검사 범위는 `complete`, `partial`, `none`입니다. 미지원 경고도 린트 성공이 아닙니다.
각 상태의 CLI 종료 코드는 순서대로 0·1·2·3입니다.
LSP는 공통 진단 코드·심각도·정밀도·문서 버전을 전달하며 상태·검사 범위 필드를 별도로 제공하지 않습니다.
빈 LSP 진단이 검사 완료를 뜻하려면 검증 설정이 있고 `cubrid` 문서로 활성화되어 있어야 합니다.

범위는 원문의 Unicode 코드 포인트 기준이며 CRLF는 두 코드 포인트입니다.
네이티브 오류는 문장 단위 정밀도이며 LSP는 원문 범위를 UTF-16으로 변환합니다.
파서 통과는 객체 존재·타입·권한·영향 행 수·서버 동작을 보장하지 않습니다.
