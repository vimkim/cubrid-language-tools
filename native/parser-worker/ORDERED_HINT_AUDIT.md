# Literal SELECT ORDERED qualification

This audit adds one argument-free block hint to profile `cubrid-11.5.0.2704-cc94778` on Linux x86-64.
The coverage revision is `bounded-query-dml-schema-engineer-ordered-v4`.
Every upstream reference below identifies the preserved source commit `cc947788d3b7dc402f46192d0f3299ddcc8563ba`.
The common initialization, literal reductions, error handling, and cleanup remain those in [AUDIT.md](AUDIT.md).
The new path does not call an optimizer or execute a query.

## Admission boundary

The scanner retains each closed `/*+ ... */` as one raw hint token with original byte offsets.
The registry routes a statement containing any hint token exclusively to the literal SELECT predicate.
A failed hint predicate cannot fall through to broader queries, DML, or schema predicates.
The native parser still receives the unchanged original statement substring.

The admitted shape has one hint token at position 1, after the top-level SELECT token.
Only space, tab, CR, and LF can separate SELECT from the hint or surround its name.
The name is exactly `ORDERED`, matched case-insensitively in ASCII.
No argument list, second name, punctuation, nested opener, or other payload is admitted.
Ordinary comments can precede SELECT or follow the hint. An ordinary comment between SELECT and the hint remains unsupported.
The SELECT body uses only the original literal alphabet, including incomplete sequences that the native parser rejects.
Names, aliases, DISTINCT, FROM, expressions, CTEs, subqueries, and other statement families gain no hint coverage.

| Form | Classification before native parsing |
| --- | --- |
| `SELECT /*+ ORDERED */ 1;` | Admitted. Native syntax and tree checks must pass. |
| `SELECT/*+ordered*/1;` | Admitted with the same native path. |
| `SELECT /*+ ORDERED */ ,;` | Admitted. Native produces S1001 for the malformed literal list. |
| `SELECT /*+ ORDERED(` followed by EOF | Scanner S1001 for an unterminated comment. No native call. |
| Closed `ORDERED(`, `ORDERED()`, `ORDERED(t)`, or nested arguments | Unsupported. Native hint syntax is not used to classify these forms. |
| Duplicate names or blocks, extra names, partial names, unknown names, nested comments | Unsupported. |
| `--+` or `//+` | Unsupported. These retain their separate line-hint exclusion. |
| Hint before SELECT, after a modifier or value, inside a nested query, or on DML or DDL | Unsupported. |

The lexer can ignore unknown or malformed hint payloads.
Unsupported classification avoids claiming that ignored text is native syntax validation.
The existing contract gives unterminated comments and quoted tokens syntax-error priority even beside unsupported syntax.

## Newly reachable pinned source

| Source | Reachable work |
| --- | --- |
| `src/parser/csql_lexer.l:1419-1455` | `/*+` enters BLOCK_HINT, saves the lexer state, and appends the payload to parser-owned bytes. Closing `*/` restores the state and calls `parser_check_hint`. The accepted payload contains only ASCII whitespace and ORDERED. Line-hint and nested-comment paths remain excluded. |
| `src/parser/csql_lexer.l:2210-2222` | `parser_check_hint` calls `pt_check_hint`. It returns SQL_HINT only when a known hint bit was found. |
| `src/parser/scanner_support.c:282-330` | `pt_initialize_hint` initializes and sorts the static hint table once. It computes local lookup offsets and lengths. The worker processes requests serially. |
| `src/parser/scanner_support.c:1270-1361` | `pt_check_hint` resets hit flags, skips whitespace, and finds ORDERED. The extra `+` branch is unreachable, so hint log printing is disabled even in a build that contains it. No user-controlled argument parser branch is reached. |
| `src/parser/scanner_support.c:1051-1125` | `hint_case_cmp` and `find_hint_token` compare ASCII spelling and require whitespace or EOF after the name. `read_hint_args` takes its initial no-parenthesis branch, sets `is_hit`, and ORs the result flag. It does not allocate argument names, resolve identifiers, or access a catalog. |
| `src/parser/csql_grammar.y:13044-13070,13376-13397` | SELECT allocates its tree and pushes the SELECT and hint node before opt_hint_list. One SQL_HINT calls `pt_get_hint` on that node. The duplicate-list reduction remains outside this predicate. |
| `src/parser/scanner_support.c:357-406` | `pt_get_hint` sees only the ORDERED hit. Its PT_SELECT branch ORs PT_HINT_ORDERED into `node->info.query.q.select.hint`. No other hint action runs. |
| `src/parser/csql_grammar.y:13195-13237` | The empty FROM production pops the SELECT and hint nodes, attaches the literal list, records query identity, and restores parser flags. The hint does not enable FROM or any later optimization stage. |
| `src/parser/scanner_support.c:337-350,957-969` | Hint cleanup frees argument lists if present. The admitted no-argument path never creates them. Conditional hint logging stays inactive. |

`IS_WHITE_SPACE` uses `char_isspace2`, which aliases `char_isspace` in `src/base/chartype.h:119`.
The admitted four ASCII whitespace characters are a deliberately narrower set.
All other literal and ordinary comment work remains covered by the original audit.

## Recovery, errors, and settings

The statement entry action calls `parser_initialize_parser_context` at `csql_grammar.y:1855`.
That helper resets `parser_hint_node_sp` with the other grammar stacks at `csql_grammar.y:23714-23731`.
Successful literal SELECT pops the node. A missing expression can leave it on the failed statement's stack, which the next statement entry resets.
`parser_main` initializes hint bookkeeping, runs `yyparse`, and calls `pt_cleanup_hint` at `csql_grammar.y:23952-23968`.
Each worker statement has a fresh parser context and clears the native error manager before parsing.

Malformed admitted literal tails use the existing lexer error path at `csql_lexer.l:1689-1895`.
The worker checks `pt_get_errors`, `pt_has_error`, `has_internal_error`, `er_errid`, and the returned tree count and kind.
A native internal flag, nonzero native error-manager value, or missing successful tree cannot become a pass.
Native tests inspect these observations and send valid hinted and unhinted requests after failures in the same process.

No admitted hint action reads or writes syntax settings.
The existing qualified settings remain unchanged and the worker verifies them before and after every parse request.
The worker continues to call parser lifecycle functions only. It never calls session execution, database login, catalog resolution, query compilation, or optimization.

## Qualification evidence and limits

The [corpus](qualification/corpus.json) contains 68 ORDERED cases in addition to the 325 retained cases.
Those 68 cases contain 11 valid results, 9 syntax errors, and 48 unsupported results.
Three syntax errors are scanner rejections for unterminated comments or a quoted token and have no native observation.
The final recovery fixture follows the rejected and malformed cases in the same worker process.
The [results](qualification/results.json) bind the actual observations to the manifest and trace.
The [ticket report](../../docs/tickets/reports/native-ordered.md) records public-interface TDD, CLI and LSP parity, artifact identity, and commands.

The syscall trace covers network, process, and openat calls for the listed corpus only.
It does not prove safety for other hints, hint arguments, all malformed SQL, other CUBRID builds, or another host.
Process isolation is not an operating-system sandbox.
