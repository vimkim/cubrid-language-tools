# Qualified coverage

[한국어](coverage.md) | **English** · [Documentation](README.en.md)

This reference describes the bounded Python development release, `0.1.0.dev0`.
The exact native profile is `cubrid-11.5.0.2704-cc94778` on Linux x86-64.
Its source commit is `cc947788d3b7dc402f46192d0f3299ddcc8563ba` and coverage revision is `bounded-query-dml-schema-engineer-v3`.
Other builds, including other 11.5 builds, need separate qualification.
The Python wheel contains no native worker, CUBRID library, or runtime assets.

## Completion

`complete` supplies ordered candidates and a replacement span for unfinished SQL and supported session commands.
Optional offline snapshots supply names, owners, columns, indexes, users, and database identity.
Completion preserves the [11.4 manual vocabulary provenance](completion-provenance.md) inherited from csql-future.
Its explicit profile argument does not select a separate version of the inherited non-hint vocabulary.
Suggestions do not establish strict 11.5 syntax support or server semantics.
Completion works without a native runtime and performs no I/O.

## Strict SQL syntax

Each example below passes parser-stage checks. The object names need not exist.
Only the listed features qualify. An admitted statement still needs a clean native tree, error state, and unchanged syntax settings.
An excluded feature produces unsupported coverage before native parsing.
Malformed input within the admitted features produces a syntax error. Ambiguous truncated forms can remain unsupported.

| Family | Example | Qualified features and limits |
| --- | --- | --- |
| SELECT | `SELECT a.id FROM absent a WHERE a.id >= 3;` | Names, qualified names, stars, aliases, DISTINCT, FROM, WHERE. No ORDER, GROUP, HAVING, LIMIT, set operations, INTO, or hints |
| Joins | `SELECT a.id FROM a LEFT JOIN b ON a.id=b.id;` | Comma, INNER, default, LEFT, RIGHT, CROSS, ON, and table parentheses. No NATURAL, FULL, USING columns, or DBLINK |
| Expressions | `SELECT (1+2)*3, '가😀', NULL;` | Integers up to 38 digits, ordinary strings, names, parentheses, arithmetic, comparisons, IS NULL, AND, OR, NOT, EXISTS. No functions, noninteger numeric literals, casts, IN, BETWEEN, LIKE, CASE, variables, or serial values |
| CTEs and subqueries | `WITH c AS (SELECT 1 AS n) SELECT n FROM c;` | Nonrecursive nested or multiple CTEs, scalar and derived queries, EXISTS and correlated names. No CTE or table-alias column lists |
| INSERT | `INSERT INTO absent (id) VALUES (1);` | VALUES rows, SELECT or CTE input. A target before a column list must be unqualified. No SET, DEFAULT, REPLACE, or duplicate-key clauses |
| UPDATE | `UPDATE absent SET id=2 WHERE id=1;` | Table references, aliases, joins, bounded assignments and WHERE. No cursor, OBJECT, ORDER, LIMIT, or immediate `SET (` |
| DELETE | `DELETE FROM absent WHERE id=1;` | Table references, aliases, WHERE, multiple-target names and joins. No USING or cursor |
| MERGE | `MERGE INTO a USING b ON a.id=b.id WHEN MATCHED THEN UPDATE SET a.id=b.id;` | Matched UPDATE and not-matched INSERT with optional arm WHERE. No DELETE arm, defaults, hints, or remote references |
| CREATE TABLE | `CREATE TABLE absent (id INTEGER, n BIGINT);` | One simple name and optional columns using INT, INTEGER, SMALLINT, BIGINT. No constraints, defaults, datatype arguments, object types, or options |
| ALTER TABLE | `ALTER TABLE absent ADD COLUMN n INTEGER;` | ADD with optional COLUMN and ungrouped integer columns. No other actions or multiple ALTER clauses |
| VIEW | `CREATE VIEW v AS SELECT id FROM absent;` | CREATE with bounded query, ALTER with `CHANGE QUERY`, and DROP. No OR REPLACE, declared columns, CHECK OPTION, or query number |
| DROP TABLE or VIEW | `DROP TABLE absent, other;` | Explicit TABLE or VIEW and comma-separated simple names. No IF EXISTS, owner qualification, ONLY, ALL, or CASCADE |
| INDEX | `CREATE INDEX ix ON absent (id DESC);` | Simple names and columns with ASC or DESC. ALTER requires `ON absent REBUILD`. DROP requires `ON absent`. No unique, reverse, expression, prefix, online, or WHERE options |
| SERIAL | `CREATE SERIAL s START WITH 1 INCREMENT BY 2;` | Original bounded integer options, ALTER options, and DROP with a name. No owner or qualified/quoted serial name. See the original audit for exact limits |
| SHOW | `SHOW TRACE;` | Exact SHOW TRACE only |
| EVALUATE | `EVALUATE 1/0;` | Bounded expressions and subqueries. No INTO or functions. The expression is never evaluated |
| Statistics | `UPDATE STATISTICS ON absent, other;` | Explicit names only. No ALL, CATALOG CLASSES, or options |
| Settings | `SET SYSTEM PARAMETERS 'ansi_quotes=no';` | Ordinary string list. Contents are never applied or checked as parameter values |
| Tracing | `SET TRACE ON OUTPUT JSON;` | ON or OFF and optional OUTPUT TEXT or JSON. Tracing remains inactive |
| Transactions | `SAVEPOINT s; ROLLBACK TO SAVEPOINT s; COMMIT WORK;` | COMMIT with optional WORK and RETAIN LOCK, ROLLBACK with optional WORK and TO SAVEPOINT, SAVEPOINT name or string. No transaction execution |

Simple quoted identifiers exclude embedded delimiters, escapes, dots, and control characters.
Functions, generic SHOW, prepared SQL, PL/CSQL, host/session variables, and other unlisted constructs remain unsupported.
The authoritative predicate details are in the [query/DML audit](../native/parser-worker/QUERY_DML_AUDIT.md),
[schema/engineer audit](../native/parser-worker/SCHEMA_ENGINEER_AUDIT.md), and [original audit](../native/parser-worker/AUDIT.md).
The retained [native corpus](../native/parser-worker/qualification/corpus.json) has 325 cases: 99 valid, 80 syntax-error, and 146 unsupported.
Its no-execution trace applies to that corpus. Process separation is not an operating-system sandbox.

## Four accepted exclusions

`SHOW COLUMNS FROM absent;`, `DESCRIBE absent;`, `DESC absent;`, and class-description `EXPLAIN absent;` remain unsupported.
The user accepted these first-profile exclusions on 2026-10-29.
The pinned client helper requires connection state and reports native error -224 when disconnected.
The original description-qualification criterion did not pass.
A separately qualified parser-only backend remains [future work](roadmap.md#language-depth).
`EXPLAIN SELECT` is also unsupported. This release's EXPLAIN production describes classes.

## CSQL batch documents

CSQL mode also admits full, column-one `;help`, `;exit`, and `;autocommit on/off` lines, ignoring case.
ASCII spaces and tabs may separate autocommit from its argument or follow these commands.
The checker inspects text after `;exit` and never applies autocommit.
Indentation, abbreviations, includes, shell commands, buffer controls, and procedure bodies remain unsupported.
Pending SQL interrupted by commands and procedural regions stay unsupported through EOF.
The [batch reference](scripts.en.md) defines lexical protection and source ranges.

## Results and positions

Library and CLI expose `valid`, `syntax-error`, `unsupported`, and `tool-error`.
Status priority is `tool-error > syntax-error > unsupported > valid`.
Coverage is `complete`, `partial`, or `none`. Unsupported warnings still fail linting.
CLI exits are 0, 1, 2, and 3 for these statuses respectively.
LSP publishes shared diagnostic codes, severity, precision, and document version. It does not expose a separate status or coverage field.
An empty LSP diagnostic list implies a checked document only when the caller configures validation and activates the document as `cubrid`.

Spans use original Unicode code points. CRLF occupies two code points.
Native errors use statement precision, and LSP converts the original spans to UTF-16.
A parser pass does not prove object existence, types, privileges, affected rows, or server behavior.

## Authoring warnings

The exact `cubrid-11.5.0.2704-cc94778` profile adds conservative SHOW and optimizer-hint authoring warnings. They do not qualify native syntax or change native coverage. The checks cover unknown complete hint names, nested or unterminated hint arguments in closed comments, hints after SELECT modifiers, and unknown or selected malformed SHOW heads. Other argument and placement errors are not checked. Unknown profiles do not receive these closed-world warnings.

A missing worker still produces its tool error alongside safely computed warnings. Ordinary comments, strings, incomplete hint comments, CSQL commands, and procedural bodies are excluded.
