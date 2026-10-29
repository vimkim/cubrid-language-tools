# CSQL command text checks report

## Result

PASS. The shared classifier admits the scoped command forms in the [ticket](../followup-csql-commands.md). The CLI and LSP consume the same classification. No public interface, native coverage identity, worker source, recipe, or packaging file changed. The checker does not execute commands or model their effects. The worktree started clean at `49479b2d0a6cf39f71498834215346d8381b82c5`; unrelated dirt was absent. The tested tree excluding this report is `2529bfe057309a43c3cd24a26550c4fd7fa72ac5`.

The command rules are one private immutable tuple of full names and permitted argument values. ASCII-only case matching and source slicing remain unchanged. No-argument time and line-output queries, invalid and extra arguments, abbreviations, indentation, and other command families remain unsupported. In particular, invalid arguments are not labeled native syntax errors, even though pinned handlers display status for non-on/off input. The source and bilingual manual audit is in the ticket.

## Evidence

Logs are under `/home/vimkim/temp/cubrid-followup-execution-6_7fcyif/csql/`.

- Before implementation, `PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_script*.py' -v` failed seven assertions because the new valid forms were classified unsupported. `baseline-tests.log` preserves the output.
- After implementation, the same command passed 16 tests, recorded in `focused-tests.log`. A second full core run used `PYTHONPATH=src /home/vimkim/gh/cubrid-language-tools/.venv/bin/python -m unittest discover -s tests -v` and passed 127 tests. See `core-tests.log`.
- `PYTHONPATH=src /home/vimkim/gh/cubrid-language-tools/.venv/bin/python -m unittest discover -s tests/native_parser -p test_scripts.py -v` passed eight actual-worker and CLI tests. See `native-tests.log`. The tests include an existing `strace` check that include and shell paths are not opened or executed.
- `PYTHONPATH=src /home/vimkim/gh/cubrid-language-tools/.venv/bin/python -m unittest discover -s tests/lsp_native -p test_script_protocol.py -v` passed four framed LSP tests. See `lsp-tests.log`. The new unsupported emoji argument has UTF-16 range line 5, characters 0 through 8. Other checks cover CRLF ranges, Korean and emoji in adjacent SQL, and inspection after exit.
- Missing worker returns `CUBRID-T1001`; an unknown profile returns `CUBRID-U1001`; malformed known commands return `CUBRID-U1002`. Pending SQL and procedural bodies remain opaque. Original classifier code-point ranges are asserted explicitly in the tests.
- `git diff --check` passed. The main checkout remained clean. Only an ignored worktree-local symlink pointed `native/parser-worker/build` to the preserved primary build during testing.

The primary worker and manifest SHA-256 values before and after testing were `9af56541bc0d90dc63ce11ae0af2122c2dfa31720e92f38992656909d5e26548` and `34b4b020ef6858c9aa0707de8617d67dfd8336f1a67220b600988e2935893dee`. The pinned library hash was `56eb36e9a46e3b6f5258974b25085b81d1679430618041343e4d979704822b33`. Source checkout was clean at `cc947788d3b7dc402f46192d0f3299ddcc8563ba`; manual checkout was `3b6ae97bfbdc664b010ffa933ded5a05b291ae03`. Worker identity verification was exercised by the actual-worker tests. These tests do not qualify other CUBRID versions or platforms.

No native corpus or worker was rebuilt. The existing shell/include syscall test does not establish an exhaustive no-execution trace for every possible input. Integration to main, publication, and installation are outside this ticket.
