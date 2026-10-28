# Reachable-action and settings audit

This audit records the common lifecycle and the original literal SELECT / CREATE
SERIAL predicates for profile **cubrid-11.5.0.2704-cc94778** on Linux x86-64.
The current revision is **bounded-query-dml-schema-engineer-v3**. Expanded
query/DML paths are qualified in [QUERY_DML_AUDIT.md](QUERY_DML_AUDIT.md).
[SCHEMA_ENGINEER_AUDIT.md](SCHEMA_ENGINEER_AUDIT.md) records bounded DDL and
engineer coverage, settings/error guards, and rejected description paths. Every upstream line below
refers to commit **cc947788d3b7dc402f46192d0f3299ddcc8563ba** in the clean,
read-only reference checkout. The source commit, source-header set, actual
compiler inputs, generated headers, library, runtime assets, worker inputs,
settings and platform are bound by [manifest.json](qualification/manifest.json)
and [build-evidence.json](qualification/build-evidence.json).

This is a source review of the reachable actions under the original two predicates.
It does not qualify all SELECT or CREATE SERIAL grammar, all grammar recovery
states, SQL execution, or a portable CUBRID runtime. The retained process trace
covers its named corpus; process separation and resource limits do not establish
an operating-system sandbox.

## Admission boundary

[coverage/scan.hpp](coverage/scan.hpp) scans the original UTF-8 text before any
native parse call. It separates statements outside strings and comments, keeps
original byte spans, and counts code points only when constructing diagnostics.
Its accepted punctuation is further limited by each family. Unterminated quotes
or comments produce a syntax diagnostic without calling native code. Ordinary
comments are retained in the native source text; hint prefixes, executable-style
comments and nested block comments deny coverage.

| Family | Token alphabet allowed before parsing | Explicit exclusions |
| --- | --- | --- |
| Literal SELECT | SELECT followed by decimal integers of at most 38 digits, ordinary single-quoted strings, NULL, commas, and a sign immediately before an integer at a list-item start; missing operands/punctuation remain eligible for native rejection | Identifiers, aliases, tables, FROM, INTO, CTEs, subqueries, parentheses, functions, arithmetic, real/monetary/typed/bit literals, host/session parameters, collation clauses, DISTINCT, ordering/limits and hints |
| CREATE SERIAL | CREATE SERIAL, one unquoted UTF-8 name token, and only START/WITH, INCREMENT/BY, MINVALUE/MAXVALUE, NOMINVALUE/NOMAXVALUE, CYCLE/NOCYCLE, CACHE/NOCACHE, COMMENT, signs, integer tokens of at most 38 digits and ordinary strings | Qualified or delimited names, owner/server clauses, dots, parameters, expressions, functions, other CREATE families and hints |

These are conservative feature predicates, not replacement parsers. They admit
malformed sequences of the listed tokens, including missing values and duplicate
options, so that the native parser decides syntax. The SERIAL name may lex as an
upstream keyword; identifier alternatives only allocate a PT_NAME, or the parser
rejects that position. The remaining token alphabet cannot enter another CREATE
family. Consecutive ordinary string tokens can reach upstream literal
concatenation; this path is included below. Unknown forms have U1002 diagnostics
and no native observations. A native PT_SELECT result alone never grants coverage.

## Initialization and common lifecycle

| Entry/action and pinned source | Reachable work and containment decision |
| --- | --- |
| [er_init, error_manager.c:680](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/base/error_manager.c#L680-L760) | Initializes message/error state. Worker supplies an absolute error-log filename inside its private directory and ER_NEVER_EXIT. Ordinary error formatting can read message catalogs and write that log. No database bootstrap is called. |
| [lang_init, language_support.c:921](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/base/language_support.c#L921-L944), [locale_support.c:7861](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/base/locale_support.c#L7861-L7910) | Initializes built-in locales and reads cubrid_locales.txt. Since envvar_confdir_file uses CUBRID/conf, the worker creates that private prefix as well as CUBRID_CONF; its locale file contains no user locale entries. No external locale plugin is requested. |
| [lang_set_charset_lang:1151](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/base/language_support.c#L1151-L1220), [client charset/collation:2767](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/base/language_support.c#L2767-L2830) | Explicit en_US.utf8 selects the built-in UTF-8 charset/collation. The parser client-charset switch is explicitly enabled. Charset/collation helper calls inspect in-process locale data, not a server. |
| [msgcat_init, message_catalog.c:501](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/base/message_catalog.c#L501-L522) | Opens the catalog names under the explicit runtime prefix. Catalog and timezone files are hash checked before initialization. |
| [sysprm_load_and_init, system_parameter.c:6385–6530,6638](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/base/system_parameter.c#L6385-L6530) | Called with db_name=NULL and the absolute private configuration path. It loads common defaults, checks/tunes parameters, and has no selected database. The ambient environment is cleared before dlopen/native initialization. Private HOME, CUBRID, CUBRID_CONF, CUBRID_DATABASES and CUBRID_TMP prevent inherited project/user configuration and registries. Timezone library identity is retained even though admitted SQL contains no temporal expression. |
| [parser_create_parser, parse_tree.c:1155–1225](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/parse_tree.c#L1155-L1225) | Allocates/registers a zeroed parser, initializes dispatch tables and scalar defaults, timestamps/random seeds and null DB_VALUEs. This does not run an expression or open a database. [parser_init_func_vectors:18388](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/parse_tree_cl.c#L18388-L18402) installs function pointers; registration itself does not call query execution. |
| [parser_parse_string_with_escapes, parse_tree_cl.c:1990–2048](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/parse_tree_cl.c#L1990-L2048) | Sets memory input callbacks and the original buffer, explicitly enables normal escapes, disables query tracing, resets positions/stack and establishes the allocation-failure jump boundary before parser_main. UTF-8 uses buffgetin rather than the EUC-KR byte-pair filter. |
| [parser_main, csql_grammar.y:23913–24051](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L23913-L24051) | Saves/restores process-global grammar/lexer state, initializes hint bookkeeping, invokes yyparse and forms a null-terminated statement array only without parser errors. Host-variable allocation is unreachable because predicates exclude parameter tokens. Calls remain serial in one owned process. |
| [stmt_list/stmt, grammar:1770–1942](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L1770-L1942), [parser_initialize_parser_context:23714](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L23714-L23731) | Reset parser-local/global stack indexes, flags and original-text bookkeeping, push produced nodes and save error positions. These actions allocate or mutate parser state only. Each scanned statement is parsed independently. |
| [parser_free_parser, parse_tree.c:1236–1300](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/parse_tree.c#L1236-L1300) | Frees parser blocks, errors, host values and locks/trace bookkeeping. DBLINK cleanup is a null-list loop ([name_resolution.c:12319](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/name_resolution.c#L12319-L12329)); lock cleanup only frees memory ([parse_tree.c:1310](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/parse_tree.c#L1310-L1327)). Admitted forms never populate remote columns, class locks or execution plans. |

The worker itself performs only manifest/file hashing, private-directory setup,
explicit dlopen/dlsym, this initialization and parser lifecycle, JSON framing and
cleanup. Native symbol names are fixed in worker.cpp. The protocol contains only
initialize, parse and shutdown; SQL text cannot select a symbol, library, path,
shell command or database.

## Literal SELECT reachable reductions

| Pinned productions/helpers | Action classification |
| --- | --- |
| [stmt_:1944–1976](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L1944-L1976), [query wrappers:12300–12477](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L12300-L12477), [select_or_subquery:12893](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L12893-L12910) | Empty WITH/order/limit/FOR UPDATE alternatives and SELECT wrapper reductions save/restore parser flags and return the same node. No table operation, CTE or nested-query branch is possible with the admitted token alphabet. |
| [select_stmt:13044–13099](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L13044-L13099), [empty FROM:13195–13237](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L13195-L13237) | Allocate PT_SELECT; push/pop SELECT and hint nodes; attach the literal list; set PT_ALL/query identity; restore flags. opt_hint_list, all_distinct and opt_select_param_list take empty alternatives ([13359–13415](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L13359-L13415)). Star and hidden-increment branches are not admitted. |
| [select/alias list:13417–13565](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L13417-L13565), [empty alias:7971](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L7971-L7987) | Link list nodes and set expression flags. Alias/name, subquery and set-expression branches require excluded tokens. A malformed list reaches the common error path rather than a catalog check. |
| [normal_expression through factor:14977–15197](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L14977-L15197), [primary:15199–15236](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L15199-L15236) | Pass-through expression levels reach literal_w_o_param. Unary minus allocates a PT_EXPR/PT_UNARY_MINUS around the integer; unary plus returns the operand. Binary operators, calls, paths, variables and parentheses cannot be consumed from the admitted SELECT alphabet. Empty opt_collation leaves the literal unchanged. No expression evaluation occurs. |
| [literal_w_o_param:20407–20465](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L20407-L20465), [unsigned_integer:21163–21217](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L21163-L21217) | NULL allocates PT_VALUE/PT_TYPE_NULL. Decimal integers become INTEGER, BIGINT or NUMERIC text by local conversion; no numeric expression runs. The predicate bounds integer spelling to 38 digits. |
| [ordinary string/concatenation:20962–20991](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L20962-L20991), [charset helper:26171–26204](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L26171-L26204) | Create PT_VALUE character literals, append consecutive CHAR_STRING bytes and assign client charset/collation. Typed/introducer/NCHAR/bit/date/json branches require denied tokens. |
| [pt_create_char_string_literal:25421–25496](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L25421-L25496), [collation helpers:25513–25639](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L25513-L25639) | Validate UTF-8, possibly allocate/combine Unicode normalization data, append parser-owned bytes and inspect built-in client collation. Default utf8_bin has no explicit COLLATE node. These helpers operate on in-memory data; they do not resolve schema/catalog objects. The caller's original text and diagnostic offsets remain unchanged. |

## CREATE SERIAL reachable reductions

| Pinned productions/helpers | Action classification |
| --- | --- |
| [CREATE SERIAL action:2910–2963](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L2910-L2963) | Allocates PT_CREATE_SERIAL and assigns the parsed name, option-container fields and optional comment. It does not create a database serial. |
| [serial_name_without_dot:5787](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L5787-L5790), [name wrapper:5680–5715](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L5680-L5715), [identifier:20624–20950](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L20624-L20950) | A single name takes the identifier alternative and marks user-specified-name metadata. IdName and nonreserved-keyword alternatives allocate PT_NAME. The dotted-name alternative is denied before parsing. No default user, user lookup or schema resolution is performed. |
| [pt_check_identifier:25341–25418](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L25341-L25418) | Checks length, bracket/dot restrictions, valid UTF-8, lowercase expansion length and possible Unicode composition using local buffers/data. Rejection here is a verified parser-stage error. |
| [option list/container:3308–3490](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L3308-L3490), [of_serial_option:3491–3542](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L3491-L3542) | Initializes/updates a local option container. Duplicate or mutually exclusive option fields report a parser error even though the message catalog labels some messages semantic. This verified local duplicate check is classified S1001; it is not a claim of general semantic validation. |
| [START/INCREMENT/MIN/MAX:11563–11649](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L11563-L11649), [CYCLE/CACHE/integer_text:11650–11703](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L11650-L11703), [unsigned_int32:21245](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L21245-L21272) | Allocate numeric text PT_VALUEs, append a minus sign locally, set boolean fields and format literal text. CACHE uses checked local 32-bit conversion and can reject overflow. No current/next serial value is read, reserved or changed. |
| [optional COMMENT:20084–20114](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L20084-L20114) | Reuses the audited ordinary-string path, changes literal type for printing and checks a fixed maximum comment length. No catalog comment is written. |

## Shared helpers, lexer and errors

Node allocation/initialization, parser-owned string/byte append, list linking,
stack save/restore and source-context macros are the common effects of these
reductions. [PARSER_SAVE_ERR_CONTEXT, grammar:277](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L277-L295)
only records offsets. Formatting is not compilation: the value-print macro in
[parse_tree.h:628](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/parse_tree.h#L628-L641)
and [literal quote helper, parse_tree_cl.c:5862–5925](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/parse_tree_cl.c#L5862-L5925)
format parser-owned values. Function-vector setup registers other printer/walker
callbacks but does not invoke unaudited statement or execution callbacks.

The lexer consumes memory through YY_INPUT ([csql_lexer.l:72](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_lexer.l#L72-L73)).
Its ordinary single-quote path, doubled quotes, newlines and escapes
([1177–1247](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_lexer.l#L1177-L1247),
[1297–1416](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_lexer.l#L1297-L1416))
append bytes only. Hint states are separated from ordinary comment states
([1419–1493](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_lexer.l#L1419-L1493));
the predicate denies all three hint prefixes before calling the lexer. PL/CSQL
states are unreachable because the admitted CREATE branch is SERIAL.

Malformed admitted token sequences can reach
[csql_yyerror_internal, lexer:1689–1895](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_lexer.l#L1689-L1895).
It bounds/quotes the token context, flushes lexer buffers, formats catalog text,
sets parser_statement_OK and appends parser error nodes. Error-list accessors
([parse_tree_cl.c:2418–2455](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/parse_tree_cl.c#L2418-L2455))
iterate those nodes. The worker checks the ordinary list, pt_has_error and
has_internal_error independently, and requires one tree of the admitted kind.
Allocation failures, internal errors, missing/partial/unexpected trees and native
process failures cannot become syntax passes. Test-only compilation sets the
real parser flag at this classification boundary after a successful parse; the
production protocol has no fault switch, and the production client rejects the
test-only manifest identity.

## Syntax settings and excluded parameter paths

| Setting | Fixed value | Reason |
| --- | --- | --- |
| charset | en_US.utf8 | Select UTF-8 input and built-in locale. |
| parser_use_client_charset | true | String creation reads explicit client charset/collation. |
| strings_have_no_escapes | false | Explicit argument to parse-string entry. |
| no_backslash_escapes | false | Ordinary lexer escape branches are fixed. |
| ansi_quotes | true | Delimited quoting remains fixed even though double-quoted tokens are not admitted. |
| pipes_as_concat | true | Pins lexer interpretation; pipe tokens remain unsupported. |
| oracle_style_empty_string | false | Pins string-literal interpretation. |
| compat_mode | 0 | Pins compatibility-dependent grammar helpers. |
| intl_check_input_string | true | Native validation of literal/name UTF-8. |
| intl_collation | utf8_bin | Uses built-in collation; no external locale/collation plugin. |
| unicode_input_normalization | false | No user-configured input normalization; original Python text/maps remain unchanged regardless of parser-owned name/string composition. |
| unicode_output_normalization | false | No user-configured output normalization. |
| query_trace | false | Prevent trace collection during parser lifetime/cleanup. |

The worker sets the boolean/integer parameters explicitly after private default
initialization and verifies their values, including intl_collation, before
reporting ready. initialize returns these settings and the client compares them
with the Python profile, alongside source/version/platform/coverage revision and
the configured manifest digest. The manifest binds the private configuration
recipe through the worker source hashes.

Other parameter reads in the grammar/lexer belong to excluded LIKE escape
productions (grammar:18001), date/number functions (23858/23885), week functions
(24575), or pipe tokens (lexer:1012). Their enabling tokens are denied. The
ENABLE_UNUSED_FUNCTION-only single-byte comparison setting is absent from this
build and is neither forced nor reported. System-parameter initialization still
sets ordinary defaults; this does not qualify unrelated grammar depending on them.

## Original predicate exclusions and common execution exclusions

Under the original predicates, FROM, table/column references, DBLINK, CTEs, nested queries, function calls,
procedural bodies, serial current/next-value expressions, INCLUDE/shell commands,
prepared execution and all other statement families fail the predicate. Their
native actions are not covered by this original audit. The additional bounded
query/DML audit supersedes those coverage exclusions only where explicitly listed.
The worker never calls the session
API, name resolution/type checking, query compiler, optimizer, DB login/restart,
network client, serial executor, schema/catalog accessor, db_compile_statement or
db_execute_statement. CSQL performs those later stages explicitly
([csql.c:2291,2355](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/executables/csql.c#L2291-L2355));
none is needed to obtain a parse tree here.

The full native shared library contains more capabilities than the worker uses.
The predicate, restricted symbol calls, error/tree classification, process
boundary, resource limits and the observed trace together support this exact
qualification. They do not make arbitrary library code safe or turn the worker
into a security sandbox. Any coverage expansion must review its newly reachable
actions and parameters, update its revision/manifest and add qualification cases.

## Diagnostic-bound delivery correction

The worker retains up to 256 ordinary findings when the request fits that bound.
Only an actual 257th finding triggers truncation. It then retains the first 255 findings and T1002.
The marker starts at the discarded 256th finding's statement boundary and covers through original EOF.
Every already-parsed decision, observation, successful kind, and full native error count remains truthful.
An unprocessed remainder becomes one nonempty contiguous rejected coverage decision.
A final-statement truncation adds no empty tail. No new parser call, symbol, grammar path, parameter, or supported feature is introduced.

Structured truncation replies require private boolean `diagnosticsTruncated: true`, exactly 256 records before deduplication, tool-error status, and partial or none coverage.
The adapter checks the count before accessing the final record. It verifies marker bounds and alignment, contiguous source accounting, native observations, kinds, manifest, and unchanged settings.
A rejected decision can omit its discarded diagnostic only when the marker covers that decision's entire original span.
An uncovered rejected decision still fails. A lower caller limit applies after full response validation and retains its first limit-minus-one findings plus T1002.
A limit of one necessarily retains only the tool error. Subsequent valid requests remain usable.
