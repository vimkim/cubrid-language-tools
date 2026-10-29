# SHOW and optimizer-hint authoring evidence

The implementation targets profile `cubrid-11.5.0.2704-cc94778`. The pinned source checkout reported commit `cc947788d3b7dc402f46192d0f3299ddcc8563ba`. The qualified worker and runtime were used through the existing ignored `native/parser-worker/build` link. Neither the native source nor worker artifacts changed.

## Regression before implementation

Commit `3bc8c42` added the public regression tests. On that commit, `.venv/bin/python -m unittest discover -s tests -p test_show_hint_authoring.py -v` failed with one failure and one error. Completion was suppressed inside `/*+ USE_NLwrong */`. The missing-runtime result had no `CUBRID-A1001` warning.

## Source audit

`csql_grammar.y` defines `parser_hint_table` at lines 24088 to 24138 and SHOW productions beginning at line 7110. The source checker compares every hint spelling and hint enum, including aliases. It also records the full SHOW production alternatives and derives all 25 possible first words. The first-word warning is enabled only for the qualified profile. The SHOW second-word rules are derived from fixed grammar prefixes in the packaged productions.

`scanner_support.c` `read_hint_args` rejects nested unquoted parentheses and unterminated arguments. The grammar places `opt_hint_list` before `all_distinct` in `select_stmt`. Those source rules support `CUBRID-A1002` and `CUBRID-A1004`. The checker does not assert broad semantic or optimizer correctness.

```sh
.venv/bin/python tools/check_show_hint_inventory.py /home/vimkim/gh/cubrid-rust/reference-cubrid-cc947788/src/parser/csql_grammar.y --write-fixture /tmp/cubrid-show-hint-fixture.y
cmp tests/fixtures/show_hint_grammar.y /tmp/cubrid-show-hint-fixture.y
.venv/bin/python -m unittest discover -s tests -p test_show_hint_authoring.py -v
```

The source comparison reported 50 hint names and 25 SHOW first words. The fixture comparison passed. The focused suite passed nine tests. Its mutation test replaces `USE_NL` with `BROKEN` in disposable fixture input and verifies that the checker exits nonzero with `inventory differs from grammar`.

## Verification

The environment used Python 3.14.0, pygls 2.1.1, lsprotocol 2025.0.0, attrs 25.4.0, and cattrs 25.3.0. Test logs are in `/tmp/cubrid-show-hints-*-final.log` and `/tmp/cubrid-show-hints-native.log`.

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m unittest discover -s tests/lsp -v
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests/native_parser -v
.venv/bin/python -m unittest discover -s tests/lsp_native -v
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests/native_parser -p test_show_hint_cli.py -v
uv build --out-dir /tmp/cubrid-show-hints-dist
```

The core suite passed 118 tests. The framed LSP suite passed 33 tests. A focused rerun checked the CRLF malformed-argument range after the full suite. The actual-native LSP suite passed seven tests. The native parser suite passed 45 tests. A separate native CLI parity test passed after that suite. A wheel installed into a separate `/tmp` virtual environment returned `USE_NL` completion and the `CUBRID-A1001` warning without a source checkout.

## Limits

Warnings do not change native status or establish syntax validity. Unknown SHOW first words and fixed second words are checked, not every trailing SHOW argument. The enabled argument check reports nested unquoted parentheses and unterminated arguments in closed hint comments. Placement checks cover hints after a SELECT modifier. Other malformed forms may receive no authoring warning. Incomplete hints and unknown profiles receive no guessed warnings. A trigger body and the rest of its classified SQL slice are suppressed conservatively. Source audit does not replace native coverage qualification. VS Code, CSQL session changes, and formatting remain outside this ticket.

## Reviewed identifier and scanner repair

Regression commit `aae6f14` exercises applied public completion edits, owner-qualified aliases, the pinned scanner counterexample, and framed LSP. Before the repair, `.venv/bin/python -m unittest discover -s tests -p test_show_hint_authoring.py -v` reported four failures. Accepting the quoted alias produced `[[order]]`, the Unicode alias produced `가가나나`, the qualified relation omitted alias `a`, and the valid two-backslash counterexample produced `CUBRID-A1002`. The framed protocol regression also reported all four failures. The logs are `/tmp/hint-repair-red-api.log` and `/tmp/hint-repair-red-lsp.log`. The explicit expected LSP offsets were corrected before the regression commit.

The repair uses the SQL identifier tokenizer for argument replacement and retains the separate ASCII hint-name span. It shares relation parsing between schema-backed and document-only alias discovery. The argument scanner now skips a backslash only before the active quote delimiter, matching the pinned `read_hint_args` implementation. The review's compiled scanner probe establishes the narrow lexical counterexample, not native parse or optimizer acceptance. The existing malformed and incomplete-comment controls remain in the tests.

The repair also removes two narrating module docstrings and corrects inherited non-hint vocabulary provenance. A framed LSP test covers a supplementary Unicode character before the edited identifier and CRLF document lines. Quote-style preservation is covered by applied public edits.

Repair verification ran against the prepared environment and the existing qualified artifacts:

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m unittest discover -s tests/lsp -v
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests/native_parser -v
.venv/bin/python -m unittest discover -s tests/lsp_native -v
.venv/bin/python tools/check_show_hint_inventory.py /home/vimkim/gh/cubrid-rust/reference-cubrid-cc947788/src/parser/csql_grammar.y
```

The core suite passed 120 tests, framed LSP passed 34, native parser passed 46, and actual-native LSP passed seven. The inventory matched 50 hint names and 25 SHOW first words. Logs are `/tmp/hint-repair-core.log`, `/tmp/hint-repair-lsp.log`, `/tmp/hint-repair-native.log`, `/tmp/hint-repair-lsp-native.log`, and `/tmp/hint-repair-inventory.log`. These checks preserve the existing qualification limits above. Installed editor acceptance belongs to the coordinator.

## Token-start boundary correction

A second independent review found that a hint argument token beginning exactly at the cursor was excluded from the replacement span. Accepting `a` at `USE_NL(|a)` duplicated the token. The same boundary affected quoted and Unicode identifiers. Commit `1f58e68` added API and framed-protocol regressions before the fix. The focused API run failed three edit-application assertions.

Including the token's left boundary corrects the replacement without changing native status or diagnostics. The complete core suite passed 120 tests. The three focused framed hint tests passed, including the new ASCII, quoted and Unicode start-of-token cases and the previous UTF-16 and escaping cases. Logs are recorded under the coordinator's `evidence/boundary-*.log` artifacts. Native worker code and coverage are unchanged.
