# Bounded schema and engineer qualification checkpoint

Profile: **cubrid-11.5.0.2704-cc94778**. Current coverage revision:
**bounded-query-dml-schema-engineer-ordered-v4**. Source commit:
**cc947788d3b7dc402f46192d0f3299ddcc8563ba**.

The user accepted the first-profile exclusions on **2026-10-29**. The disconnected
runtime cannot safely qualify DESCRIBE, DESC, class-description EXPLAIN, or
SHOW COLUMNS. These forms return unsupported before native parsing. A separately
qualified parser-only backend remains later work. The original description
criterion did not pass. This audit qualifies the revised bounded scope below.
It extends [AUDIT.md](AUDIT.md) and [QUERY_DML_AUDIT.md](QUERY_DML_AUDIT.md).
It preserves their query/DML and CREATE SERIAL limits.
Revision v4 adds only the separately audited [literal SELECT ORDERED](ORDERED_HINT_AUDIT.md)
path. The registry rejects hints before any schema or engineer predicate runs.

## Admission boundary and exact supported features

[coverage/schema_engineer.hpp](coverage/schema_engineer.hpp) checks tokens before
parser creation. [registry.hpp](coverage/registry.hpp) binds each predicate to its
expected native kind. A produced native kind never grants coverage by itself.
The scanner preserves original text and the previous comment, quote and operator
exclusions. Simple quoted names use the existing `ordinary_identifier` rule.
Names can reference absent objects. Qualification does not prove their existence,
types, privileges or server behavior.

| Family | Qualified features | Limits |
| --- | --- | --- |
| CREATE TABLE | One simple table name, optional parenthesized columns with INT/INTEGER, SMALLINT or BIGINT | No datatype arguments, object types, constraints, defaults, AS query, methods, partitioning or options |
| ALTER TABLE | ADD, optional COLUMN, integer columns without grouping | No other ALTER action, defaults, constraints or multiple ALTER clauses |
| CREATE VIEW | One simple view name, optional AS followed by the existing bounded query features | No OR REPLACE, column declaration list, CHECK OPTION or comments |
| ALTER VIEW | One simple view name, CHANGE QUERY followed by the existing bounded query features | No query number, AS alternative, column declarations or other actions |
| DROP TABLE / VIEW | Explicit TABLE or VIEW, comma-separated simple names | No IF EXISTS, owner qualifiers, ONLY/ALL or CASCADE |
| CREATE INDEX | Simple index name, ON simple table name, parenthesized simple columns with optional ASC/DESC | No UNIQUE/REVERSE, function/prefix/expression index, WHERE, online or invisible options |
| ALTER / DROP INDEX | Simple index name, ON simple table name. ALTER requires REBUILD | No other index actions or DROP column list |
| ALTER SERIAL | Original CREATE SERIAL option alphabet and integer/string limits | No owner clause, qualified or quoted name |
| DROP SERIAL | Simple name after SERIAL | No IF EXISTS or qualified name. Bare DROP SERIAL is unsupported because SERIAL can instead be a table identifier |
| SHOW | Exact SHOW TRACE | Other SHOW forms remain unsupported, including truncated SHOW and extra TRACE tokens |
| EVALUATE | Existing bounded expression and subquery features | No INTO, functions, variables or serial values. The expression is never evaluated |
| Statistics | UPDATE STATISTICS ON comma-separated simple names | No ALL/CATALOG CLASSES or statistics options |
| Settings | SET SYSTEM PARAMETERS with ordinary string list | Strings remain SQL data. Their contents are never interpreted as parameters |
| Tracing | SET TRACE ON/OFF, optional OUTPUT TEXT/JSON | No other tracing statements |
| Transactions | COMMIT, optional WORK and RETAIN LOCK. ROLLBACK, optional WORK and TO SAVEPOINT. SAVEPOINT accepts a name or ordinary string | No transaction settings, host/session variables, function or arithmetic savepoint expressions |

Predicates also admit incomplete or malformed sequences within these feature
bounds. The native parser still decides syntax. Some truncated features remain
unsupported when a safe family cannot be identified. In particular, native
`DROP SERIAL` parses as PT_DROP for a table named SERIAL. The predicate therefore
requires a following name before selecting PT_DROP_SERIAL.

The table predicate permits names only in the target or column-name positions.
An object datatype cannot enter through an ordinary or quoted identifier.
A parenthesis after an identifier can introduce only the CREATE TABLE target's
column list or the CREATE INDEX ON target's column list. Integer type words
cannot introduce parentheses. Index column names cannot introduce function or
prefix-length parentheses. Unicode, quoted names and intervening comments use
the same token positions.

VIEW predicates inspect the DDL prefix separately, then pass the untouched query
tokens to `bounded_query`. DDL words never extend the query alphabet. EVALUATE
uses the same query feature checks with a synthetic SELECT token only inside
the feature predicate. Native parsing still receives the original EVALUATE text.
The previous structural keyword-parenthesis rules remain deliberate exceptions.
For example, `AS(1)` is a native syntax rejection, whereas `INTEGER(1)`,
`TABLE(1)`, `QUERY(1)`, named calls and quoted/comment-hidden calls are unsupported.

## Complete reduction candidates and manual context proof

[audit_schema_engineer.py](audit_schema_engineer.py) reuses the pinned Bison
production extractor. It computes alphabet-productive complete reductions and
retains source/action lines, RHS symbols, action hashes and call candidates.
[schema-engineer-reductions.json](qualification/schema-engineer-reductions.json)
contains **370 distinct candidate reductions across 20 alphabets**.
It includes rejected SHOW COLUMNS and description candidates, labeled as rejected.
Its bindings cover grammar, lexer, helper sources, generators and predicate headers.
The build manifest independently binds production inputs and helper sources.
The trace report binds the inventories, audit documents and qualification tools.

The inventory is deliberately broader than admission. It retains generic
functions, object datatypes and alternate ALTER VIEW reductions that context
checks exclude. It does not prove those candidates safe. The following manual
review narrows those candidates and covers prefix, midrule and error actions.
No claim of arbitrary-grammar or memory-safety proof follows from this inventory.

Every upstream line below refers to the pinned source commit above.

| Reachable productions / helpers | Manual action and context review |
| --- | --- |
| [Statement wrappers, grammar 1770–2120](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L1770-L2120) | Existing parser resets, node stack, source positions and statement dispatch. Fixed first/second words exclude unrelated statement families. Malformed prefixes can allocate hint nodes, push messages and set parser flags. They cannot enter login, catalog, compiler or execution APIs. |
| [CREATE TABLE, 2576–2636](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L2576-L2636) | Allocate PT_CREATE_ENTITY before the table prefix, push/pop the hint node, attach name/columns, then gather constraints. Hints, inheritance, class attributes, options, methods, partitions and CREATE AS branches take empty alternatives. The CREATE AS error-print branch is unreachable. |
| [CREATE VIEW, 2637–2676](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L2637-L2676), [AS query wrappers, 9040–9095](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L9040-L9095) | Allocate PT_CREATE_ENTITY, attach the view name and parser-owned query list, then gather constraints. Prefix positions exclude column declarations and OR REPLACE. All query actions retain the previous audit. Commas may link parser-owned query nodes. |
| [ALTER TABLE / VIEW, 3586–3682](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L3586-L3682), [ADD, 6168–6302](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L6168-L6302), [CHANGE QUERY, 6507–6549](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L6507-L6549) | Allocate/save PT_ALTER, attach integer attribute nodes or the already-audited query, copy the target name for list-based ALTER, and gather constraints. The saved ALTER/attribute pointers at 23431–23462 only assign/read parser-global pointers. Multiple ALTER clauses are excluded by the ADD alphabet. CHANGE QUERY's numeric-selector branch is excluded by the query-prefix test. |
| [Attribute lists/definitions, 9846–9951 and 10084–10183](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L9846-L9951), [integer datatypes, 19170–19193](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L19170-L19193) | Link columns, allocate PT_ATTR_DEF and store scalar datatype enums. Optional constraints/comments/order take empty alternatives. INT aliases INTEGER in the keyword table. Parenthesis and name-position guards exclude padding, collection/object types and expressions. Missing types or commas use local parser errors. |
| [pt_gather_constraints, parse_tree_cl.c 4727–4848](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/parse_tree_cl.c#L4727-L4848) | Inspect existing node kinds and relink attribute/constraint/index lists. Under these predicates, only ordinary attributes or null lists are populated. No schema lookup occurs. Unexpected node kinds use the existing internal-error flag. |
| [DROP entities, grammar 4493–4510](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L4493-L4510), [class specifications, 5501–5680](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L5501-L5680) | Allocate PT_DROP and ordinary PT_SPEC/list nodes. IF EXISTS and CASCADE options remain false. No object deletion or class lookup occurs. |
| [CREATE INDEX, 2677–2836](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L2677-L2836), [sort list, 4777–4790](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L4777-L4790) | Allocate index/spec/sort nodes and store names/directions. The index expression alphabet has only names and parentheses, with no calls, literals or operators. `parser_count_prefix_columns` at 23681–23710 counts existing nodes. Its function/prefix conversion and error branches cannot occur with a function-free list. Reverse/unique/where/online/invisible/comment options remain empty. |
| [ALTER INDEX rebuild, 3865–3915](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L3865-L3915), [DROP INDEX, 4511–4574](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L4511-L4574) | Allocate the corresponding node/spec, store index/table names, and mark REBUILD. Other ALTER actions require excluded words. DROP column lists require excluded parentheses. No index maintenance runs. |
| [ALTER SERIAL, 3799–3864](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L3799-L3864), [DROP SERIAL, 4625–4637](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L4625-L4637) | Reuse the original serial-option numeric conversion, container and duplicate-option checks. Allocate PT_ALTER_SERIAL/PT_DROP_SERIAL and attach names/options. OWNER is excluded. No serial read, advance, creation or deletion occurs. |
| [EVALUATE, 11055–11069](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L11055-L11069) | Allocate PT_EVALUATE and attach the existing expression tree. INTO takes the empty alternative. No expression evaluator is called, including for division by zero. All expression/subquery/error helpers retain the query audit. |
| [Statistics, 4794–4857](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L4794-L4857) | Allocate PT_UPDATE_STATS and attach syntactic name lists. Options take their empty alternative. No statistics acquisition, update or catalog enumeration occurs. |
| [SET SYSTEM PARAMETERS, 2192–2204](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L2192-L2204) | Allocate PT_SET_SYS_PARAMS and attach the ordinary string list. The parameter parser and setter are not called. Unknown parameter names and values can therefore pass syntax checking. |
| [SET TRACE, 2331–2372](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L2331-L2372) | Allocate PT_QUERY_TRACE, storing only ON/OFF and output-format enums. This does not enable tracing or change a runtime parameter. |
| [SHOW TRACE, 7381–7391](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L7381-L7391), [pt_make_query_show_trace, parser_support.c 10368–10401](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/parser_support.c#L10368-L10401) | Allocate PT_SELECT and PT_TRACE_STATS expression nodes. Set parser-local read-only/statistics flags and clear parser-local query_trace. The trace evaluator is not called. Exact token matching excludes every generic SHOW metadata/authorization callback. |
| [Transactions, 10987–11054](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L10987-L11054) | Allocate PT_COMMIT_WORK, PT_ROLLBACK_WORK or PT_SAVEPOINT. Store retain-lock flag or syntactic savepoint name/string. No transaction manager, lock operation, rollback or commit function runs. |

The existing identifier checks at grammar 20624–20950 and 25341–25419 allocate
names, validate length/UTF-8, and optionally compose parser-owned strings.
The admitted DDL names do not trigger `pt_set_user_specified_name` during parsing.
Copy/walk/free callbacks for PT_CREATE_ENTITY, PT_ALTER, PT_ATTR_DEF, PT_DATA_TYPE,
index, serial, transaction and engineer nodes traverse their child fields.
They copy scalar state and free parser-owned allocations. Their catalog, DB_VALUE,
execution-plan, remote-column and workspace-object fields remain unpopulated.
Common allocation failures use the parser jump/error path. Native error flags,
unreported errors, missing trees and unexpected kinds retain T1002 classification.

Malformed and incomplete input can execute midrule allocations and flag/message
stack operations before a final reduction. Fixed prefixes and per-context tokens
still exclude the dangerous productions in those prefixes. Existing lexer and
local syntax-error helpers format message-catalog text, append parser errors,
and free lexer/parser buffers. No error handler in these bounded paths fetches
schema, starts a session or evaluates submitted SQL.

## Rejected class-description paths: concrete blocker

[DESCRIBE / DESC / EXPLAIN, grammar 7796–7802](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L7796-L7802)
share the class-description production at 7213–7255. This release does not
provide generic `EXPLAIN SELECT` through this production.
SHOW COLUMNS uses the same query-construction helper.

The transitive path is:

1. [pt_make_query_show_columns, parser_support.c 6995–7145](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/parser_support.c#L6995-L7145) creates schema-query nodes and local integer/string DB_VALUE placeholders.
2. [pt_dbval_to_value, parse_dbi.c 573–599](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/parse_dbi.c#L573-L599) unconditionally calls db_value_clone and ignores its return.
3. [db_value_clone, db_macro.c 1460–1472](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/compat/db_macro.c#L1460-L1472) checks connection state before cloning.
4. [CHECK_CONNECT_ERROR, db.h 79–90](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/compat/db.h#L79-L90) sets ER_OBJ_NO_CONNECT and returns. The CS library defaults to disconnected at db_macro.c:93. error_code.h:298 defines that error as -224.

The additional `pt_set_user_specified_name` callback at parser_support.c:10754
can read the current schema name at 11031. No user/schema state is fabricated.
Its later-schema construction and the value-clone error prevent qualification.
The identifier-specific DESCRIBE helper at 8092 also delegates to the same path.

[rejected-candidates.json](qualification/rejected-candidates.json) records an
explicit probe before the final predicates excluded these candidates.
All four cases produced one tree, no parser error and no internal-error flag.
The error manager reported **-224** in every case. The strengthened worker
returned T1002 with no successful statement kind. Subsequent SHOW TRACE and
SELECT requests reported zero native error. This evidence is labeled rejected
and is separate from the qualified corpus. It does not authorize these paths.

SHOW TABLES also reads the selected database name at parser_support.c:6451–6508.
SHOW CREATE TABLE calls schema lookup/printer code at 7170–7265.
Current-user SHOW GRANTS reads authorization identity at 7647–7665.
Generic SHOW invokes metadata, optional DBA checks and argument resolution at
6831–6910. All remain unsupported before parsing. No broad PT_SELECT test admits
a SHOW statement. No catalog or connection error becomes an ordinary S1001 error.

## Settings, errors, lifecycle and traces

No newly admitted form reads a new syntax parameter. DDL integer types store
enums. EVALUATE and VIEW queries reuse the query audit. SET/TRACE/transactions
store syntax nodes only. The existing settings remain explicit and unchanged.
`Runtime::verify_settings` checks actual parameters at initialization and before
and after every parse request. It also checks UTF-8 client charset and the parser
client-charset flag. Successful parse replies include `syntaxSettingsUnchanged`.
Public tests parse SET strings that request altered quoting, escapes, pipes,
tracing and collation. Subsequent requests retain the qualified settings.

Before each parser allocation, the worker clears the prior error-manager state.
[er_clear, error_manager.c 1202–1210](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/base/error_manager.c#L1202-L1210)
only clears the current thread's error level.
[er_errid, 1826–1844](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/base/error_manager.c#L1826-L1844)
returns its error ID. The worker records `nativeErrorId` after parsing.
Any nonzero value becomes T1002. The adapter requires an integer observation
and rejects an error-bearing response presented as success. No error ID is ignored.
Every admitted observation in the final corpus reports zero native error.

The final [corpus](qualification/corpus.json) retains the original 179 cases.
Only two expectations change because DROP TABLE is now qualified.
The added cases cover valid, malformed, incomplete, Unicode and mixed documents,
context exclusions, destructive SQL text, arbitrary SET strings, division by zero,
and every blocked description spelling. Statement spans remain original code
points with `statement` precision. Native byte columns are never editor offsets.

[results.json](qualification/results.json) and [syscalls.strace](qualification/syscalls.strace)
retain the actual final corpus and syscall trace. The runner checks exact fixture
status/kinds/admission, zero native errors, settings invariance, graceful shutdown,
one worker exec, zero descendants, zero network calls and no external writable
opens. Traces qualify this corpus and host only. Process separation is not an OS
sandbox. No CSQL, compiler, session, catalog lookup, expression evaluator, database
or daemon is used for qualification.
