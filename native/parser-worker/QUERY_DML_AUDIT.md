# Bounded query and DML qualification

Profile: **cubrid-11.5.0.2704-cc94778**. Coverage revision:
**bounded-query-dml-create-serial-v2**. All source links refer to the exact
read-only commit **cc947788d3b7dc402f46192d0f3299ddcc8563ba**. The generated
headers, library, runtime assets, settings, platform and production inputs stay
bound by the manifest and embedded digest. This extends the common lifecycle,
literal and CREATE SERIAL review in [AUDIT.md](AUDIT.md).

## Admission and published limits

`coverage::admit` chooses a per-family feature predicate before parser creation.
A native statement kind never grants coverage. Each admitted statement must
still produce exactly one tree of the expected kind, no ordinary error, no
internal-error flag and no unreported error flag. Missing/partial/unexpected
trees fail. Statements are parsed separately; their original UTF-8 bytes are
passed unchanged. Diagnostics use original Unicode code-point statement spans
with explicit `statement` precision.

| Family | Qualified features | Deliberate limits |
| --- | --- | --- |
| SELECT | Names, qualified names, `*`/`name.*`, aliases, DISTINCT, FROM, WHERE | No ORDER/GROUP/HAVING/LIMIT, set operations, SELECT INTO/TO, hints, hierarchy or FOR UPDATE |
| Joins | Comma, INNER/default JOIN, LEFT/RIGHT with optional OUTER, CROSS JOIN; ON conditions; table parentheses | No NATURAL/FULL/SEMI/ANTI, USING columns, index hints or DBLINK |
| Expressions | Integers of at most 38 digits; ordinary strings and adjacent ordinary strings; NULL; names; parentheses; unary/binary +/-, */; =, <>, !=, <, >, <=, >=; IS [NOT] NULL; AND/OR/NOT/EXISTS | No functions, real/exponent/bit/hex/national/charset-prefixed/typed literals, concatenation/bit operators, IN/BETWEEN/LIKE, casts/collations, case expressions, pseudocolumns, host/session variables or serial values |
| CTEs | Nonrecursive WITH, multiple/nested definitions and AS query | No RECURSIVE or CTE column lists; native parser acceptance does not prove recursive/reference semantics |
| Subqueries | Scalar, derived tables, comparisons, EXISTS, correlated name references | Local multicolumn scalar and ON-subquery rejections remain parser errors; no catalog resolution |
| INSERT | Optional INTO, ordinary target with optional simple column list, VALUE/VALUES rows (including empty rows), SELECT/CTE input and parenthesized VALUES queries | A target immediately followed by a column list must be one unqualified name; no SET, DEFAULT, REPLACE, duplicate-key, partition or output-variable clauses |
| UPDATE | Table references/aliases/joins, assignments with the audited expressions/subqueries, optional WHERE | No cursor, OBJECT, defaults, hints, ORDER/LIMIT. `SET (` is denied because SET also introduces a collection function. Parenthesized assignments after other assignments can reach the reviewed local tuple reduction |
| DELETE | Ordinary/aliased table references, optional WHERE, explicit multiple-target names and joins | No USING, cursor, hints or LIMIT |
| MERGE | INTO/USING ordinary or derived table specs, ON; matched UPDATE and/or not-matched INSERT in either order, optional per-arm WHERE | No DELETE, defaults, hints or remote references. INSERT/UPDATE may occur only directly after THEN |
| CREATE SERIAL | Original literal/options subset from AUDIT.md | Unchanged |

The common query keyword alphabet is exactly SELECT, WITH, AS, FROM, WHERE,
DISTINCT, JOIN, INNER, LEFT, RIGHT, OUTER, CROSS, ON, AND, OR, NOT, EXISTS, IS and
NULL. INSERT adds INSERT/INTO/VALUE/VALUES; UPDATE adds UPDATE/SET; DELETE adds
DELETE; MERGE adds MERGE/INTO/USING/WHEN/MATCHED/THEN/UPDATE/SET/INSERT/VALUE/VALUES.
Every other native keyword is denied even when it could act as a nonreserved
identifier. Ordinary nonkeyword names remain eligible for native identifier
validation. Integer and source-size limits are independent.

The frozen [keyword inventory](coverage/keywords.hpp) is generated from both
`keyword.c` and the explicit word rules in `csql_lexer.l`. Its source hashes are
retained in the header; build.py regenerates the expected bytes in memory and
refuses a mismatch. The generator, header and all production predicates are
manifest inputs. This avoids treating an unaudited native keyword as an ordinary
name. The exact source pin and library digest remain mandatory; no nearby-build
fallback exists.

Simple double-quoted, bracket-quoted and backtick-quoted identifiers contain only
letters/digits/underscore/space/UTF-8 bytes between the delimiters. Embedded
delimiters, backslash, dot and ASCII control spellings are outside this revision.
The scanner does not interpret their contents as keywords. CURRENT_VALUE,
CURRVAL, NEXT_VALUE and NEXTVAL are denied case-insensitively even as quoted
names, so the special serial rewrite cannot become reachable through a dot.
Native identifier validation still decides length, UTF-8 and identifier legality.

All ordinary/quoted name-before-`(` pairs are denied except an INSERT target
column list at the initial target position. Keyword-before-`(` pairs require an
explicit structural list. LEFT/RIGHT are SQL join words but also reserved string
functions; SET introduces `SET(subquery)`; MATCHED is a nonreserved identifier
that can name a generic function. All three routes are denied. INSERT is allowed
only initially or directly after MERGE THEN; INTO only at token index one.
VALUES/VALUE query productions remain reachable in INSERT/MERGE and are reviewed
below. FROM/JOIN/USING/AS/SELECT and predicate parentheses reach only the listed
table/query/condition productions; they cannot introduce generic functions.

The scanner preserves compound operator identities before feature checking:
`->`, `->>`, `||`, `&&`, `<<`, `>>`, `<=>`, `?:` and `:=` cannot become admitted
single-character operations. Numeric-dot and adjacent numeric-word sequences
are denied so native real/exponent/bit/hex lexing cannot bypass the integer
limit. Name/string introducers are denied. Comments disappear only from feature
tokens; the original comments remain in native text. All three hint prefixes,
executable-style block comments and nested block comments deny coverage.
Strings retain their contents, semicolons and comment markers. Unterminated
quoted tokens/comments receive S1001 without a native call.

These checks do not recognize SQL syntax. Missing operands, names, JOIN/ON
parts, malformed clauses, unbalanced parentheses, local arity/type errors and
other malformed arrangements of admitted features still enter the native
parser. Unknown features produce U1002 and zero native observations. A malformed
sequence that includes a denied feature remains unsupported, apart from the
contract's independent unterminated-token handling.

## Reproducible reduction inventory

[audit_query_dml.py](audit_query_dml.py) reads the pinned Bison source, removes
C actions/comments without changing source line identity, then computes
productive complete reductions per terminal alphabet from `stmt_done`. The
retained [inventory](qualification/query-dml-reductions.json) has **251 distinct
reductions**: query 162, INSERT 206, UPDATE 176, DELETE 174, MERGE 242. It records
each RHS, source/action lines, action SHA-256 and call candidates, plus the
grammar/tool hashes and each family's terminal/nonterminal/reduction identities.
Alias spellings in keyword.c are retained independently when mapping terminals.

This is a conservative inventory, not a proof of parser safety. It deliberately
overapproximates the initial-token/adjacency checks and includes harmless local
alternatives such as alias/CTE column lists and INSERT SET in the MERGE alphabet.
Its explicit context exclusions are generic_function_id, insert_expression,
reserved_func, table_set_function_call, to_param and paren_plus. The feature
checks above justify those exclusions. Midrule actions on incomplete prefixes,
shared helpers, lexer states, printers/walkers and error paths also require the
manual review below; a productive-reduction calculation alone does not cover
them. No arbitrary grammar recovery state is claimed qualified.

Reproduce without changing source or runtime:

~~~sh
python3 native/parser-worker/audit_query_dml.py \
  --source /home/vimkim/gh/cubrid-rust/reference-cubrid-cc947788 \
  --output native/parser-worker/qualification/query-dml-reductions.json
~~~

## Newly reachable actions and helpers

Each grouped row includes its empty/wrapper/list alternatives. Common statement
boot, allocation, value/string/Unicode helpers, error access, cleanup and native
internal-error classification retain the original AUDIT.md review.

| Exact pinned source | Reachable effects and excluded branches |
| --- | --- |
| [stmt_done/list/stmt/stmt_, grammar:1762–2030](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L1762-L2030) | Reset grammar stacks/flags, original-text and password-offset bookkeeping, attach top-level WITH, push resulting nodes and restore datetime/transaction/cache flags. No password/PL/SQL actions are enabled. Malformed prefixes can run this same initialization and the family node-allocation midrules. UPDATE STATISTICS requires the denied STATISTICS token before its action. No new execute/prepare/call/set statement branch is enabled. |
| [name/spec reductions:4302–4320,5018–5737](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L5018-L5737), [identifiers:20587–20950](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L20587-L20950) | Allocate PT_SPEC/PT_NAME, attach aliases, source/derived tables, dotted owner strings, star metadata and user-specified-name flags; link parenthesized class/table lists. Name qualification copies text, never obtains the current DB user. Only empty partition/index-hint branches apply. CLASS/ALL/EXCEPT/TABLE/JSON_TABLE/DBLINK/@/right-arrow paths are denied. The nonreserved MATCHED name alternative is local allocation; MATCHED function calls are denied. |
| [joins:5031–5215](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L5031-L5215) | Link specs; set join enums and ON nodes; save/restore pseudocolumn/instnum/within-join flags. Missing outer-join conditions append a local parser error. ON's parser_walk_tree uses only pt_check_instnum_pre/post, [parser_support.c:1831–1868](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/parser_support.c#L1831-L1868): skip nested SELECTs, inspect operator enums and set a bool. It does not evaluate an expression. |
| [query wrappers:12053–12815](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L12053-L12815), [select/with/from:12889–13545](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L12889-L13545) | esql/csql query wrappers push/pop parser-owned SELECT/orderby/hint stacks and flags. SELECT attaches expression/from/where lists, query identity, DISTINCT and ANSI/dummy flags. WITH/CTE allocate PT_WITH_CLAUSE/PT_CTE and link definitions; RECURSIVE is absent. Aliases copy name text. Empty FROM's star rejection and scalar-subquery column-count rejection are local parser errors. Hidden serial increments cannot be populated. Table operations, output parameters, hierarchy/group/having/index/ordering/limit/for-update clauses take empty alternatives or are denied. |
| [derived-table simplification:23731–23805](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L23731-L23805) | parser_remove_dummy_select moves an existing spec/alias out of a redundant `SELECT *` wrapper and frees detached nodes. CTE-bearing queries are not removed. No rewrite compiler or schema lookup runs. FOR UPDATE's guarded error branch is unreachable. |
| [WHERE/empty options:13874–14892](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L13874-L14892) | WHERE saves/restores local checks and returns the condition. Group/having/order/limit/rollup/hint/for-update/increment options remain empty. Context-pruned CTE/alias attribute-list alternatives only link already allocated names. |
| [expressions:13546–13575,14963–15305](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L14963-L15305), [constructor:22777–22848](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L22777-L22848) | Link expression lists and allocate operator nodes for +/-/*/division/unary-minus; unary-plus returns its child. No arithmetic evaluation occurs (`1/0` parses successfully). Parentheses set flags or wrap an expression-set PT_VALUE, [25880–25915](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L25880-L25915). COLLATE is denied, so the modifier helper's nonempty branch is unreachable. Function/case/typed/pseudo/session/subinsert branches are denied. |
| [condition/comparison/null:17660–18472](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L17660-L18472), [subquery/path:18601–18858](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L18601-L18858) | AND/OR/NOT/EXISTS/comparison/null nodes are allocated, logical types checked, join-type flags pushed/popped, and scalar-query metadata set. Subqueries in ON and wrong scalar arity report local errors. Dotted paths allocate PT_DOT_; all four special serial names are denied before this action. `==` reaches the explicit local syntax-error/YYABORT path. `(+)`, right-arrow, comparison qualifiers, LIKE/set/IN/BETWEEN/RANGE and generic functions are denied. |
| [comparison helpers, parse_tree_cl.c:4835–5345](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/parse_tree_cl.c#L4835-L5345) | pt_get_subquery_list/pt_get_expression_count inspect existing lists. pt_select_list_to_one_col wraps multiple projected expressions as a sequence; ORDER/LIMIT/ORDERBY_NUM-dependent derived-table rewrite is unreachable. pt_check_set_count_set checks local list dimensions recursively; pt_rewrite_set_eq_set rewrites row comparisons into conjunctions of existing expressions. They can append local count errors, allocate/copy/free nodes, but do not resolve names, typecheck against a DB or execute. |
| [INSERT:6622–7099](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L6622-L7099) | Allocate PT_INSERT/PT_SPEC/PT_NODE_LIST; attach target, attribute, value/query lists; prepend/reverse row links to preserve order. Empty rows read the pinned COMPAT_MODE=0 and create an empty value-list node. SELECT input uses the same audited query wrappers. SET/default/replace/duplicate-key/subinsert/output-variable/remote actions cannot be selected by the family predicate. The inventory's INSERT SET overapproximation also only builds local attr/value/spec lists; DEFAULT branches require a denied token. |
| [VALUES query:12946–13047](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L12946-L13047) | INSERT/MERGE can contain parenthesized VALUES queries. These allocate a PT_SELECT with value-query flags and PT_NODE_LIST rows, link expressions and locally reject a direct subquery row. No row is inserted or evaluated. Retained fixtures cover this separate query branch. |
| [UPDATE/assignment:7808–8155](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L7808-L8155) | Allocate PT_UPDATE and PT_ASSIGN, attach specs/assignments/WHERE; manage hint/order stacks. Tuple assignment alternatives flatten/copy parser nodes and check local element counts; a SET-immediate tuple is conservatively denied. Cursor/OBJECT/default/ORDER/LIMIT/hints are denied; their guarded walkers/error branches therefore do not run. |
| [DELETE:8157–8320](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L8157-L8320), [pt_check_unique_names, name_resolution.c:4392–4453](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/name_resolution.c#L4392-L4453), [name comparison:8366–8438](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/name_resolution.c#L8366-L8438) | Allocate/attach PT_DELETE/target/spec/condition lists, copy an existing name for an implicit single target and set reusable-OID name metadata. The duplicate-name helper walks only PT_SPEC/PT_NAME lists and compares strings (including dotted qualification) using intl_identifier_casecmp. Its file name does not imply name resolution: no class prefetch/catalog access is called. Duplicate aliases are a verified S1001 parser-stage rejection. USING/cursor/LIMIT branches are denied. |
| [MERGE:8322–8417](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L8322-L8417) | Allocate PT_MERGE, attach INTO/USING/ON nodes, reuse audited update/insert lists and attach per-arm WHERE. Either arm or both orders are local pointer assignment. DELETE branches are denied. No merge executor/compiler/transaction API is called. |

## Shared helper closure, error paths and settings

[parser_make_expression](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L22777-L22848)
and [PICE](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar_scan.h#L35-L59)
set logical types, attach child pointers and run instnum/groupbynum compatibility
checks. [parser_support.c:1632–1820](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/parser_support.c#L1632-L1820)
inspects node/operator enums and flags only; orderbynum maps to instnum.
Constructors never evaluate submitted expressions. Node/list allocation,
append/reverse, source-context macros and stack save/restore only mutate parser
memory. [pt_node_list:407–420](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/parser_support.c#L407-L420)
allocates a list wrapper; [reverse/link:22851–22881](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L22851-L22881)
only changes next pointers. Dynamic stack growth reports allocation failures
through the existing error manager; it does not touch a DB.

[parser_walk_tree/copy_tree](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/parse_tree_cl.c#L943-L1435)
uses registered apply callbacks to traverse child pointers. The reachable
NAME/DOT/EXPR/VALUE/SPEC/SELECT/WITH/CTE/node-list callbacks only walk fields.
Copy callbacks allocate nodes, copy scalar state and repair a temporary CTE
pointer list; [19659–19674](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/parse_tree_cl.c#L19659-L19674)
frees that list. Parse-only nodes have null XASL/catalog/workspace fields;
cross-parser/workspace-value/JSON-column copy branches are not populated by this
coverage. Freeing nodes releases parser-owned resources. Function registration
does not invoke semantic/compiler callbacks.

Local malformed-input actions can call pt_short_print/parser_print_tree for an
error context. The [short printer:3358–3380](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/parse_tree_cl.c#L3358-L3380)
formats at most its context limit; registered ordinary name/spec/expression/query
printers append text from existing nodes. [Name printing:14181–14448](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/parse_tree_cl.c#L14181-L14448)
does not request a current username under the default custom_print=0.
[CTE printing:18154–18288](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/parse_tree_cl.c#L18154-L18288)
formats existing lists; is_parsing_static_sql remains false, so its static-SQL
rewrite branch is excluded. Error printing does not compile a query.

The lexer gains only ordinary/delimited identifiers, operator punctuation and
the listed keyword rules ([word/operator/name rules:167–1154](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_lexer.l#L167-L1154),
[quoted rules:1177–1416](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_lexer.l#L1177-L1416)).
Dot-following names may lex as IdName even when keyword-shaped; the conservative
inventory still rejects unlisted keywords before that native path. Quoted states
append bytes, validate names and return the matching identifier token.
ANSI_QUOTES=true is now actively used for double-quoted identifiers. Existing
ordinary-string escape/charset/collation/normalization checks remain unchanged.

The existing [lexer error routine:1689–1895](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_lexer.l#L1689-L1895)
bounds/quotes token context, formats local message-catalog text, flushes buffers,
sets parser flags and appends errors. Explicit grammar errors use the same error
lists. Wrong logical operands, missing outer ON, duplicate DELETE aliases,
scalar-column counts, ON subqueries and row-assignment dimensions are all local
checks verified in this source; their S1001 classification does not imply general
semantic checking. Native message wording is never a decision key. Allocation,
internal flags, unreported errors, unexpected/missing trees, crashes, deadlines,
bad identities and malformed responses retain T1001/T1002/T1003 classification.
No known catalog-dependent error is reclassified as syntax; catalog-dependent
constructs remain U1002 before native parsing.

No new syntax parameter is introduced. Empty INSERT rows read COMPAT_MODE, which
was already explicitly set/verified to 0. ANSI_QUOTES=true, no_backslash_escapes=false,
pipes_as_concat=true, oracle_style_empty_string=false, query_trace=false,
UTF-8/client-charset/built-in utf8_bin and disabled input/output normalization
remain the exact settings in AUDIT.md and initialize. LIKE/date/number/week
parameter branches are unreachable because their enabling tokens/functions are
denied. Worker bounds, cancellation, serial request ownership and graceful
shutdown are unchanged.

## No-execution evidence and practical limits

[corpus.json](qualification/corpus.json) is the fixed expected behavior used by
both public protocol and NativeWorker adapter tests and by the traced runner.
[results.json](qualification/results.json) retains actual replies, admitted
decisions, native error/tree flags and statement kinds. [syscalls.strace](qualification/syscalls.strace)
records the entire corpus, including nonexistent relation names, DELETE/MERGE
text, arithmetic division by zero, valid/malformed/incomplete/Unicode and mixed
documents. The runner requires exactly one worker exec, zero descendants, zero
network operations and zero writable opens outside its private prefix. It also
checks normal shutdown. Evidence-file digests bind the corpus, audits and tools.
No submitted SQL is sent to CSQL, compiled, executed or used to open a database.

The source boundary calls only parser creation, parse-string, error access and
parser cleanup after controlled initialization. No login/restart/session,
schema/catalog fetch, DBLINK, compiler, optimizer, query executor or daemon entry
is called. Parser-stage passes deliberately do not prove object existence,
column types, privileges, CTE binding, valid assignment targets or row effects.
Process isolation is not a syscall sandbox. Traces are evidence for the retained
corpus and this exact Linux x86-64 build, not universal runtime containment.
