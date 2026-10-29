# Offline CSQL batch scripts

[한국어](scripts.md) | **English**

The shared `Validator` checks CSQL batch documents without executing SQL or commands.
The CLI and LSP use the same classification and diagnostics.
Use [CLI settings](lint-cli.en.md) or [LSP settings](lsp.en.md) to select `scriptMode: csql`.
Files with a `.csql` suffix select CSQL mode by default.
Other paths, stdin, and untitled documents select SQL mode unless settings override that choice.

## Qualified commands

Only these complete command lines qualify:

```text
;help
;exit
;autocommit on
;autocommit off
;commit
;rollback
;time on
;time off
;line-output on
;line-output off
```

Command names and arguments are case-insensitive for these forms.
Each command must start in column one, outside a string, comment, or quoted identifier.
LF, CRLF, and the final EOF can terminate a command line.
One or more ASCII spaces or tabs must separate autocommit, time, or line-output from its argument.
Trailing ASCII spaces or tabs are also permitted.
Indentation, abbreviations, extra arguments, non-ASCII suffix whitespace, and additional semicolons remain unsupported.
The interpreter accepts more spellings, but this subset deliberately excludes them, including no-argument time and line-output queries. Invalid arguments remain unsupported, not syntax errors.

The checker inspects the whole document.
It continues after an accepted exit command and does not change session or transaction state. Accepting commit or rollback checks the text shape only.
Commands, empty documents, and unsupported-only documents still require a qualified profile and available worker.
Unknown profiles produce `CUBRID-U1001`.
Missing workers or runtime assets produce tool errors.

Includes, shell commands, `!` commands, buffer controls, and PL/CSQL remain unsupported.
The checker never reads include targets, starts a shell, requests credentials, or connects to a database.
SQL mode sends the original document to the qualified SQL worker without admitting CSQL commands.

## Boundaries and conservative recovery

Commands inside multiline lexical blocks remain SQL content.
The scanner preserves single quotes, double quotes, backticks, brackets, and ordinary comments.
It accounts for doubled delimiters and the profile's backslash escapes in single-quoted strings.
Semicolons inside these blocks do not end SQL statements.
Only LF starts another batch line. CRLF occupies two original code points.

Complete SQL statements can precede or follow command lines:

```sql
SELECT '가😀;';
;help
SELECT 2
```

The final SQL statement does not need a semicolon if the native parser accepts it.
SQL chunks retain their exact original text, including comments and line endings.
Native statement ranges can include leading trivia.

A command inside pending SQL requires conservative recovery:

```text
SELECT
;help
1;
```

The interpreter can preserve this SQL buffer across an informational command.
The checker currently marks the pending statement and everything after it as unsupported through EOF.
It does not report syntax errors from separately parsed fragments.
This limit also applies to parenthesized SQL and unsupported commands with unknown buffer effects.
Put each command between terminated SQL statements to avoid this limit.

The checker also keeps procedural regions opaque through EOF.
These regions start with `CREATE [OR REPLACE] PROCEDURE`, `FUNCTION`, or `PACKAGE`, or with `BEGIN` or `DECLARE`.
Internal semicolons do not expose independent successful SQL checks.
The checker does not attempt recovery after the procedural region's apparent end.
An unterminated quote or comment inside a procedural region retains a syntax diagnostic alongside its unsupported diagnostic.

## Original offsets and results

All library spans count Unicode code points from zero and exclude the end offset.
The classifier does not normalize Unicode, case, whitespace, or newlines.
It returns immutable parts whose spans refer to the original document:

```python
from cubrid_language.scripts import classify

text = ";help\r\nSELECT '가😀;';"
for part in classify(text):
    original_slice = text[part.span.start:part.span.end]
    print(part.kind, part.span, original_slice)
```

Part kinds are `sql`, `command`, and `unsupported`.
`lexical_error` identifies an unterminated SQL lexical block without granting syntax acceptance.
Classification is pure and performs no filesystem, process, or database operations.
Strict checking requires the configured [Validator](lint-cli.en.md#python-interfaces).

The Validator translates each SQL chunk's local diagnostics into original document offsets.
It retains statement precision instead of inventing token precision.
CLI JSON exposes those code-point spans. Human CLI locations use one-based code-point columns.
The LSP converts the same spans into UTF-16 protocol ranges.

Syntax and unsupported diagnostics can coexist.
Status priority is `tool-error`, `syntax-error`, `unsupported`, then `valid`.
A later worker failure retains earlier findings and subsequent classified unsupported regions.
Coverage is complete only when every region can be checked under the selected profile.
The document diagnostic limit applies across command boundaries.
Exceeding that limit returns a tool error with an explicit truncation message.

## Qualification and source boundary

Script classification adds no native grammar family.
The matching native worker and manifest still determine SQL coverage for the exact 11.5 profile.
See the [native guide](../native/parser-worker/README.md) for its current coverage revision and build inputs.
No database, CSQL interpreter, or daemon participates in script qualification.

The [boundary preflight](orchestration/script-boundaries-preflight.md) records the pinned manual and source evidence.
The Korean manual and pinned batch dispatch agree that lexical blocks protect embedded command prefixes.
The manual allows leading blanks, but the pinned raw batch dispatcher checks the first character.
The checker therefore retains its narrower, unindented subset.
The pinned command parser trims argument whitespace.
This audit also qualifies ASCII spaces and tabs before required arguments and after the full supported forms. The [command ticket](tickets/followup-csql-commands.md) records the pinned source and manual evidence for the additional forms.

Run the default tests, mandatory native/CLI tests, framed LSP tests, and mandatory native LSP tests separately:

```sh
just test
just test-native-parser
just test-lsp
just test-lsp-native
```

Missing native artifacts or optional LSP dependencies fail their mandatory suites.
Default tests remain independent of those optional prerequisites.
